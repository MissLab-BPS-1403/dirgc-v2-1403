import time

from .logging_utils import log_info, log_warn, log_error
from .settings import (
    AUTO_LOGIN_RESULT_TIMEOUT_S,
    BLOCK_UI_SELECTOR,
    HASIL_GC_LABELS,
    LOGIN_PATH,
    MATCHAPRO_HOST,
    SSO_HOST,
    TARGET_URL,
)


class ActivityMonitor:
    def __init__(self, page, idle_timeout_ms, stop_event=None, timeout_scale=1.0):
        self.page = page
        self.idle_timeout_s = idle_timeout_ms / 1000
        self.last_activity = time.monotonic()
        self.stop_event = stop_event
        self.timeout_scale = timeout_scale if timeout_scale and timeout_scale > 0 else 1.0

    def _check_stop(self):
        if self.stop_event and self.stop_event.is_set():
            raise RuntimeError("Run stopped by user.")

    def mark_activity(self, _reason=None):
        self.last_activity = time.monotonic()

    def idle_check(self):
        self._check_stop()
        if time.monotonic() - self.last_activity > self.idle_timeout_s:
            raise RuntimeError(
                "Idle timeout reached (5 minutes without activity)."
            )

    def scale_timeout(self, timeout_s):
        if timeout_s is None:
            return None
        return timeout_s * self.timeout_scale

    def wait_for_condition(self, condition, timeout_s=None, poll_ms=500):
        timeout_s = self.scale_timeout(timeout_s)
        start = time.monotonic()
        while True:
            if condition():
                return True
            if timeout_s is not None and time.monotonic() - start > timeout_s:
                return False
            self.idle_check()
            self.page.wait_for_timeout(poll_ms)

    def bot_click(self, selector_or_locator):
        self._check_stop()
        self.mark_activity("bot")
        if isinstance(selector_or_locator, str):
            self.page.click(selector_or_locator)
        else:
            selector_or_locator.click()

    def bot_fill(self, selector, value):
        self._check_stop()
        self.mark_activity("bot")
        self.page.fill(selector, "" if value is None else str(value))

    def bot_select_option(self, selector, **kwargs):
        self._check_stop()
        self.mark_activity("bot")
        self.page.select_option(selector, **kwargs)

    def bot_goto(self, url):
        self._check_stop()
        self.mark_activity("bot")
        self.page.goto(url, wait_until="domcontentloaded")


def install_user_activity_tracking(page, mark_activity):
    page.expose_function("reportActivity", lambda: mark_activity("user"))
    page.add_init_script(
        """
        (() => {
          function isRelevantInput(target) {
            if (!target) return false;
            const id = (target.id || "").toLowerCase();
            const name = (target.name || "").toLowerCase();
            const autocomplete = (target.autocomplete || "").toLowerCase();
            if (id === "username" || id === "password") return true;
            if (name === "username" || name === "password") return true;
            if (autocomplete === "one-time-code") return true;
            const markers = ["otp", "verif", "kode", "mfa"];
            return markers.some((marker) => id.includes(marker) || name.includes(marker));
          }

          function reportIfCredentialInput(event) {
            const target = event.target;
            if (!isRelevantInput(target)) return;
            if (window.reportActivity) {
              window.reportActivity();
            }
          }
          document.addEventListener("input", reportIfCredentialInput, true);
          document.addEventListener("change", reportIfCredentialInput, true);
        })();
        """
    )


def ensure_on_dirgc(
    page,
    monitor,
    use_saved_credentials,
    credentials,
):
    def is_on_target():
        return page.url.startswith(TARGET_URL)

    def is_on_login_page():
        return MATCHAPRO_HOST in page.url and LOGIN_PATH in page.url

    def is_on_matchapro():
        return MATCHAPRO_HOST in page.url

    def is_on_sso_login():
        if SSO_HOST in page.url:
            return True
        return page.locator("#kc-login").count() > 0

    def is_on_otp_challenge():
        if not is_on_sso_login():
            return False
        otp_selectors = [
            "input[autocomplete='one-time-code']",
            "input[name*='otp']",
            "input[id*='otp']",
            "input[name*='verif']",
            "input[id*='verif']",
            "input[name*='kode']",
            "input[id*='kode']",
        ]
        for selector in otp_selectors:
            locator = page.locator(selector)
            if locator.count() > 0 and locator.first.is_visible():
                return True
        text_markers = [
            "OTP",
            "Kode OTP",
            "kode otp",
            "verification code",
            "kode verifikasi",
        ]
        for marker in text_markers:
            locator = page.locator(f"text={marker}")
            if locator.count() > 0 and locator.first.is_visible():
                return True
        return False

    def click_if_present(selector):
        locator = page.locator(selector)
        if locator.count() == 0:
            return False
        monitor.bot_click(locator.first)
        return True

    def attempt_auto_login(username, password):
        if not username or not password:
            log_warn(
                "Saved credentials missing; switching to manual login."
            )
            return False

        if not monitor.wait_for_condition(
            lambda: page.locator("#username").count() > 0, 15
        ):
            log_warn("Login fields not found; switching to manual login.")
            return False

        monitor.bot_fill("#username", username)
        monitor.bot_fill("#password", password)
        monitor.bot_click("#kc-login")

        error_selectors = [
            "#input-error",
            "#kc-error-message",
            ".kc-feedback-text",
            ".alert-error",
            ".pf-c-alert__title",
        ]

        start = time.monotonic()
        while True:
            if is_on_matchapro():
                return True
            for selector in error_selectors:
                locator = page.locator(selector)
                if locator.count() > 0 and locator.first.is_visible():
                    return False
            if time.monotonic() - start > monitor.scale_timeout(
                AUTO_LOGIN_RESULT_TIMEOUT_S
            ):
                return False
            monitor.idle_check()
            page.wait_for_timeout(500)

    allow_autofill = use_saved_credentials
    autofill_attempted = False
    username, password = credentials or (None, None)

    monitor.bot_goto(TARGET_URL)

    while True:
        if is_on_target():
            log_info("On target page.", url=page.url)
            return

        if is_on_login_page():
            if click_if_present("#login-sso"):
                log_info("Redirecting to SSO login.")
                monitor.wait_for_condition(
                    lambda: is_on_sso_login() or is_on_matchapro(),
                    timeout_s=30,
                )
                continue
            monitor.wait_for_condition(
                lambda: page.locator("#login-sso").count() > 0
                or not is_on_login_page(),
                timeout_s=10,
            )
            continue

        if is_on_sso_login():
            if allow_autofill and not autofill_attempted:
                autofill_attempted = True
                if attempt_auto_login(username, password):
                    monitor.wait_for_condition(is_on_matchapro, timeout_s=60)
                    continue
                allow_autofill = False
                log_warn("Auto-fill login failed; switching to manual login.")

            if is_on_otp_challenge():
                log_info("OTP required; waiting for manual input.")
            else:
                log_info("Waiting for manual login.")
            monitor.wait_for_condition(is_on_matchapro)
            continue

        if is_on_matchapro() and not is_on_target():
            monitor.bot_goto(TARGET_URL)
            continue

        monitor.wait_for_condition(lambda: False, timeout_s=2)


def is_visible(page, selector):
    locator = page.locator(selector)
    return locator.count() > 0 and locator.first.is_visible()


def wait_for_block_ui_clear(page, monitor, timeout_s=15):
    monitor.wait_for_condition(
        lambda: page.locator(BLOCK_UI_SELECTOR).count() == 0
        or not is_visible(page, BLOCK_UI_SELECTOR),
        timeout_s=timeout_s,
    )


def ensure_filter_panel_open(page, monitor):
    if is_visible(page, "#search-idsbr"):
        return
    toggle = page.locator("#toggle-filter")
    if toggle.count() > 0:
        monitor.bot_click(toggle.first)
        monitor.wait_for_condition(
            lambda: is_visible(page, "#search-idsbr"), timeout_s=10
        )


def apply_filter(page, monitor, idsbr, nama_usaha, alamat):
    ensure_filter_panel_open(page, monitor)

    def get_results_snapshot():
        header_locator = page.locator(".usaha-card-header")
        count = header_locator.count()
        first_text = ""
        last_text = ""
        if count > 0:
            try:
                first_text = header_locator.first.inner_text().strip()
            except Exception:
                first_text = ""
            if count > 1:
                try:
                    last_text = (
                        header_locator.nth(count - 1)
                        .inner_text()
                        .strip()
                    )
                except Exception:
                    last_text = ""
            else:
                last_text = first_text
        return count, first_text, last_text

    def results_changed(previous_snapshot):
        return get_results_snapshot() != previous_snapshot

    def wait_for_results(previous_snapshot, timeout_s=15):
        monitor.wait_for_condition(
            lambda: is_visible(page, ".empty-state")
            or is_visible(page, ".no-data")
            or is_visible(page, ".no-results")
            or results_changed(previous_snapshot),
            timeout_s=timeout_s,
        )
        wait_for_block_ui_clear(page, monitor, timeout_s=timeout_s)
        return page.locator(".usaha-card-header").count()

    def retry_results_if_slow(count, timeout_s=5):
        if count <= 1:
            return count
        previous_snapshot = get_results_snapshot()
        updated = monitor.wait_for_condition(
            lambda: is_visible(page, ".empty-state")
            or is_visible(page, ".no-data")
            or is_visible(page, ".no-results")
            or results_changed(previous_snapshot),
            timeout_s=timeout_s,
        )
        if not updated:
            return count
        wait_for_block_ui_clear(page, monitor, timeout_s=timeout_s)
        return page.locator(".usaha-card-header").count()

    def set_filter_values(idsbr_value, nama_value, alamat_value):
        monitor.mark_activity("bot")
        page.evaluate(
            """
            ({ idsbrValue, namaValue, alamatValue }) => {
              const setValue = (selector, value) => {
                const input = document.querySelector(selector);
                if (!input) return;
                input.value = value || "";
              };

              setValue("#search-idsbr", idsbrValue);
              setValue("#search-nama", namaValue);
              setValue("#search-alamat", alamatValue);

              const dispatch = (selector) => {
                const input = document.querySelector(selector);
                if (!input) return;
                input.dispatchEvent(new Event("input", { bubbles: true }));
                input.dispatchEvent(new Event("change", { bubbles: true }));
              };

              dispatch("#search-idsbr");
              dispatch("#search-nama");
              dispatch("#search-alamat");
            }
            """,
            {
                "idsbrValue": idsbr_value or "",
                "namaValue": nama_value or "",
                "alamatValue": alamat_value or "",
            },
        )

    def search_with(idsbr_value, nama_value, alamat_value):
        previous_snapshot = get_results_snapshot()
        set_filter_values(idsbr_value, nama_value, alamat_value)
        monitor.wait_for_condition(lambda: False, timeout_s=0.5)
        return wait_for_results(previous_snapshot)

    if idsbr:
        count = search_with(idsbr, "", "")
        if count > 1:
            log_info(
                "Results not unique; rechecking for slow loading.",
                count=count,
            )
            count = retry_results_if_slow(count)
        if count == 1:
            return count
        if nama_usaha or alamat:
            if count == 0:
                log_warn(
                    "IDSBR not found; retry with idsbr + nama_usaha + alamat."
                )
            else:
                log_warn(
                    "Multiple results for IDSBR; retry with idsbr + nama_usaha + alamat.",
                    count=count,
                )
            return search_with(idsbr, nama_usaha, alamat)
        return count

    return search_with("", nama_usaha, alamat)


def hasil_gc_select(page, monitor, code):
    if code is None:
        return False
    monitor.wait_for_condition(
        lambda: page.locator("#tt_hasil_gc").count() > 0, timeout_s=15
    )
    select_locator = page.locator("#tt_hasil_gc")
    value_locator = select_locator.locator(f'option[value="{code}"]')
    if value_locator.count() > 0:
        monitor.bot_select_option("#tt_hasil_gc", value=str(code))
        return True
    label = HASIL_GC_LABELS.get(code)
    if label:
        monitor.bot_select_option("#tt_hasil_gc", label=label)
        return True
    return False



def add_usaha(
    page,
    monitor,
    idsbr,
    nama_usaha,
    alamat,
    provinsi,
    kabupaten,
    kecamatan,
    kelurahan,
    latitude,
    longitude,
):
    """
    Tambah Usaha Baru - ID fields: tt_nama_usaha, tt_alamat, tt_latitude, tt_longitude
    Wilayah menggunakan Select2: container-tambah-usaha, container-kabupaten-kota-tt, etc
    Button: save-tambah-usaha-btn
    """
    log_info("Opening Tambah Usaha form.")
    
    tambah_button = page.locator("button#tambah-usaha-btn")
    if tambah_button.count() == 0:
        tambah_button = page.locator("button", has_text="Tambah Usaha")
    
    if tambah_button.count() == 0:
        log_warn("Tombol Tambah Usaha tidak ditemukan.")
        return False
    
    wait_for_block_ui_clear(page, monitor, timeout_s=15)
    
    try:
        tambah_button.first.scroll_into_view_if_needed()
    except Exception:
        pass
    
    try:
        monitor.bot_click(tambah_button.first)
    except Exception as exc:
        log_warn("Gagal klik tombol Tambah Usaha.", error=str(exc))
        return False
    
    form_ready = monitor.wait_for_condition(
        lambda: page.locator("#modal-tambah-usaha").count() > 0
        and page.locator("#modal-tambah-usaha").first.is_visible(),
        timeout_s=30,
    )
    
    if not form_ready:
        log_warn("Modal Tambah Usaha tidak muncul.")
        return False
    
    monitor.wait_for_condition(lambda: False, timeout_s=1.5)
    log_info("Filling Tambah Usaha form.")
    
    def safe_fill(field_id, value, field_name):
        if not value:
            return
        locator = page.locator(f"#{field_id}")
        if locator.count() == 0:
            log_warn(f"{field_name} (#{field_id}) not found.")
            return
        try:
            locator.first.click()
            locator.first.fill("")
            page.wait_for_timeout(300)
            locator.first.type(str(value))
            log_info(f"Filled {field_name}.", value=value)
        except Exception as exc:
            log_error(f"Failed {field_name}.", error=str(exc))
    
    def safe_select2(container_id, value, field_name):
        if not value:
            return
        try:
            container = page.locator(f"#{container_id}")
            if container.count() == 0:
                log_warn(f"{field_name} container not found.")
                return
            monitor.bot_click(container.first)
            page.wait_for_timeout(500)
            search = page.locator("input.select2-search__field")
            if search.count() == 0:
                page.keyboard.press("Escape")
                return
            search.first.fill(value)
            page.wait_for_timeout(1000)
            result = page.locator(".select2-results__option:not(.select2-results__option--disabled)").first
            if result.count() > 0:
                monitor.bot_click(result)
                log_info(f"Selected {field_name}.", value=value)
            else:
                log_warn(f"No results {field_name}.")
                page.keyboard.press("Escape")
        except Exception as exc:
            log_error(f"Failed select {field_name}.", error=str(exc))
            try:
                page.keyboard.press("Escape")
            except:
                pass
    
    safe_fill("tt_nama_usaha", nama_usaha, "Nama Usaha")
    safe_fill("tt_alamat", alamat, "Alamat")
    
    if provinsi:
        safe_select2("container-tambah-usaha", provinsi, "Provinsi")
        page.wait_for_timeout(2000)
    
    if kabupaten:
        safe_select2("container-kabupaten-kota-tt", kabupaten, "Kabupaten")
        page.wait_for_timeout(2000)
    
    if kecamatan:
        safe_select2("container-kecamatan-tt", kecamatan, "Kecamatan")
        page.wait_for_timeout(2000)
    
    if kelurahan:
        safe_select2("container-kelurahan-desa-tt", kelurahan, "Kelurahan")
        page.wait_for_timeout(1000)
    
    safe_fill("tt_latitude", latitude, "Latitude")
    safe_fill("tt_longitude", longitude, "Longitude")
    
    # Scroll modal ke bawah untuk tombol Simpan terlihat
    try:
        page.locator("#modal-tambah-usaha .modal-body").first.evaluate("el => el.scrollTop = el.scrollHeight")
    except:
        pass
    
    simpan = page.locator("button#save-tambah-usaha-btn")
    if simpan.count() == 0:
        simpan = page.locator("button", has_text="Simpan")
    
    if simpan.count() == 0:
        log_warn("Tombol Simpan tidak ditemukan.")
        return False
    
    wait_for_block_ui_clear(page, monitor, timeout_s=15)
    
    try:
        simpan.first.scroll_into_view_if_needed()
    except:
        pass
    
    page.wait_for_timeout(500)
    log_info("Clicking Simpan.")
    
    try:
        monitor.bot_click(simpan.first)
    except Exception as exc:
        log_warn("Failed click Simpan.", error=str(exc))
        return False
    
    swal_result = None
    warning_handled = False
    
    def find_swal():
        nonlocal swal_result, warning_handled
        popup = page.locator(".swal2-popup")
        if popup.count() == 0 or not popup.first.is_visible():
            return False
        try:
            text = popup.first.inner_text().lower()
        except:
            return False
        
        # Cek warning - HARUS KLIK OK
        if "warning" in text and ("draft" in text or "table" in text or "cek" in text):
            if not warning_handled:
                log_warn("Warning terdeteksi - akan klik OK untuk melanjutkan.")
                warning_handled = True
                swal_result = "warning"
                return True
            return False
        
        if "berhasil" in text or "sukses" in text:
            swal_result = "success"
            return True
        if "duplikat" in text or "sudah ada" in text:
            swal_result = "duplicate"
            return True
        if "gagal" in text or "error" in text:
            swal_result = "error"
            return True
        return False
    
    monitor.wait_for_condition(find_swal, timeout_s=30)
    
    # CASE 1: Warning - klik OK, scroll, centang checkbox, simpan lagi
    if swal_result == "warning":
        log_info("Klik OK pada warning popup.")
        ok = page.locator(".swal2-confirm")
        if ok.count() > 0:
            try:
                monitor.bot_click(ok.first)
            except:
                pass
        
        page.wait_for_timeout(1500)
        
        # Scroll modal ke bawah
        log_info("Scroll modal ke bawah.")
        try:
            page.locator("#modal-tambah-usaha .modal-body").first.evaluate("el => el.scrollTop = el.scrollHeight")
        except:
            pass
        
        page.wait_for_timeout(1000)
        
        # Centang checkbox - coba berbagai selector
        log_info("Mencari dan centang checkbox konfirmasi.")
        checkbox_found = False
        
        # Selector berdasarkan foto: form-check-label for-tambah fc-modalin
        checkbox_selectors = [
            "input[type='checkbox'].fc-modalin",
            "input[type='checkbox']#for-tambah",
            "input.form-check-input.fc-modalin",
            ".form-check-input",
            "input[type='checkbox']",
        ]
        
        for selector in checkbox_selectors:
            checkboxes = page.locator(selector)
            if checkboxes.count() > 0:
                # Cari checkbox yang belum dicentang dan visible
                for i in range(checkboxes.count()):
                    cb = checkboxes.nth(i)
                    try:
                        if cb.is_visible() and not cb.is_checked():
                            cb.check()
                            log_info(f"Checkbox dicentang menggunakan selector: {selector}")
                            checkbox_found = True
                            break
                    except:
                        continue
                if checkbox_found:
                    break
        
        if not checkbox_found:
            log_warn("Checkbox konfirmasi tidak ditemukan atau sudah dicentang.")
        
        page.wait_for_timeout(1000)
        
        # Klik Simpan lagi
        log_info("Klik Simpan (kedua kali) setelah centang checkbox.")
        simpan2 = page.locator("button#save-tambah-usaha-btn")
        if simpan2.count() == 0:
            simpan2 = page.locator("button", has_text="Simpan")
        
        if simpan2.count() == 0:
            log_warn("Tombol Simpan (kedua) tidak ditemukan.")
            return False
        
        try:
            simpan2.first.scroll_into_view_if_needed()
        except:
            pass
        
        page.wait_for_timeout(500)
        
        try:
            monitor.bot_click(simpan2.first)
        except Exception as exc:
            log_warn("Failed click Simpan kedua.", error=str(exc))
            return False
        
        # Tunggu popup hasil (success/error/duplicate)
        page.wait_for_timeout(2000)
        swal_result = None
        
        def find_swal_final():
            nonlocal swal_result
            popup = page.locator(".swal2-popup")
            if popup.count() == 0 or not popup.first.is_visible():
                return False
            try:
                text = popup.first.inner_text().lower()
            except:
                return False
            
            if "berhasil" in text or "sukses" in text:
                swal_result = "success"
                return True
            if "duplikat" in text or "sudah ada" in text:
                swal_result = "duplicate"
                return True
            if "gagal" in text or "error" in text:
                swal_result = "error"
                return True
            return False
        
        monitor.wait_for_condition(find_swal_final, timeout_s=30)
    
    # CASE 2: Success
    if swal_result == "success":
        log_info("Usaha berhasil ditambahkan.")
        ok = page.locator(".swal2-confirm")
        if ok.count() > 0:
            try:
                monitor.bot_click(ok.first)
            except:
                pass
        monitor.bot_goto(TARGET_URL)
        return True
    elif swal_result == "duplicate":
        log_warn("Duplikasi.")
        ok = page.locator(".swal2-confirm")
        if ok.count() > 0:
            try:
                monitor.bot_click(ok.first)
            except:
                pass
        monitor.bot_goto(TARGET_URL)
        return False
    else:
        log_warn("Submit failed/timeout.")
        monitor.bot_goto(TARGET_URL)
        return False


