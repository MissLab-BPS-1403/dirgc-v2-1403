from .browser import (
    apply_filter,
    ensure_on_dirgc,
    hasil_gc_select,
    is_visible,
    wait_for_block_ui_clear,
)
from .excel import load_excel_rows
from .logging_utils import log_error, log_info, log_warn
from .matching import select_matching_card
from .run_logs import build_run_log_path, write_run_log
from .settings import TARGET_URL


def process_excel_rows(
    page,
    monitor,
    excel_file,
    use_saved_credentials,
    credentials,
    start_row=None,
    end_row=None,
    progress_callback=None,
):
    run_log_path = build_run_log_path()
    run_log_rows = []
    try:
        rows = load_excel_rows(excel_file)
    except Exception as exc:
        log_error("Failed to load Excel file.")
        run_log_rows.append(
            {
                "no": 0,
                "idsbr": "",
                "nama_usaha": "",
                "alamat": "",
                "keberadaanusaha_gc": "",
                "latitude": "",
                "longitude": "",
                "status": "error",
                "catatan": str(exc),
            }
        )
        write_run_log(run_log_rows, run_log_path)
        log_info("Run log saved.", path=str(run_log_path))
        return
    if not rows:
        log_warn("No rows found in Excel file.")
        write_run_log(run_log_rows, run_log_path)
        log_info("Run log saved.", path=str(run_log_path))
        return

    total_rows = len(rows)
    start_row = 1 if start_row is None else start_row
    end_row = total_rows if end_row is None else end_row
    if start_row < 1 or end_row < 1:
        log_error(
            "Start/end row must be >= 1.",
            start_row=start_row,
            end_row=end_row,
        )
        write_run_log(run_log_rows, run_log_path)
        log_info("Run log saved.", path=str(run_log_path))
        return
    if start_row > end_row:
        log_warn(
            "Start row is greater than end row; nothing to process.",
            start_row=start_row,
            end_row=end_row,
        )
        write_run_log(run_log_rows, run_log_path)
        log_info("Run log saved.", path=str(run_log_path))
        return
    if start_row > total_rows:
        log_warn(
            "Start row exceeds total rows; nothing to process.",
            start_row=start_row,
            total=total_rows,
        )
        write_run_log(run_log_rows, run_log_path)
        log_info("Run log saved.", path=str(run_log_path))
        return
    if end_row > total_rows:
        log_warn(
            "End row exceeds total rows; clamping.",
            end_row=end_row,
            total=total_rows,
        )
        end_row = total_rows

    rows = rows[start_row - 1 : end_row]
    selected_rows = len(rows)
    stats = {
    "total": selected_rows,
    "processed": 0,
    "skipped_no_results": 0,
    "skipped_gc": 0,
    "skipped_duplikat": 0,
    "skipped_no_tandai": 0,
    "hasil_gc_set": 0, # Berhasil Tandai
    "hasil_gc_edited": 0, # Berhasil Tandai via Edit
    "hasil_gc_skipped": 0,
    "hasil_gc_invalid_coordinate": 0,
}
    log_info(
        "Start processing rows.",
        total=selected_rows,
        start_row=start_row,
        end_row=end_row,
    )
    if progress_callback:
        try:
            progress_callback(0, selected_rows, 0)
        except Exception:
            pass

    for offset, row in enumerate(rows):
        batch_index = offset + 1
        excel_row = start_row + offset
        stats["processed"] += 1
        status = None
        note = ""

        idsbr = row["idsbr"]
        nama_usaha = row["nama_usaha"]
        alamat = row["alamat"]
        latitude = row["latitude"]
        longitude = row["longitude"]
        hasil_gc = row["hasil_gc"]

        # Log tambahan untuk mengintip isi data row
        log_info(
            "Row content loaded.",
            nama=nama_usaha or "-",
            lat=latitude or "-",
            long=longitude or "-",
            gc_status=hasil_gc or "-"
        )
        
        log_info(
            "Processing row.",
            _spacer=True,
            _divider=True,
            row=batch_index,
            total=selected_rows,
            row_excel=excel_row,
            idsbr=idsbr or "-",
        )
        ensure_on_dirgc(
            page,
            monitor=monitor,
            use_saved_credentials=use_saved_credentials,
            credentials=credentials,
        )

        try:
            log_info(
                "Applying filter.",
                idsbr=idsbr or "-",
                nama_usaha=nama_usaha or "-",
                alamat=alamat or "-",
            )
            result_count = apply_filter(page, monitor, idsbr, nama_usaha, alamat)
            log_info("Filter results.", count=result_count)

            selection = select_matching_card(
                page, monitor, idsbr, nama_usaha, alamat
            )
            if not selection:
                log_warn("No results found; skipping.", idsbr=idsbr or "-")
                stats["skipped_no_results"] += 1
                status = "gagal"
                note = "No results found"
                continue

            header_locator, card_scope = selection
            try:
                header_locator.scroll_into_view_if_needed()
            except Exception:
                pass
            monitor.bot_click(header_locator)

            if card_scope.count() == 0:
                card_scope = page

            if (
                card_scope.locator(".gc-badge", has_text="Sudah GC").count()
                > 1 #mengabaikan Sudah GC
            ):
                log_info("Skipped: Sudah GC.", idsbr=idsbr or "-")
                stats["skipped_gc"] += 1
                status = "skipped"
                note = "Sudah GC"
                continue

            if card_scope.locator(
                ".usaha-status.tidak-aktif", has_text="Duplikat"
            ).count() > 0:
                log_info("Skipped: Duplikat.", idsbr=idsbr or "-")
                stats["skipped_duplikat"] += 1
                status = "skipped"
                note = "Duplikat"
                continue



            # PATCH untuk update Koordinat
            # 1. Ambil Lat/Long dari Web
            lat_raw = card_scope.locator(".gc-info-item", has_text="Latitude").locator(".gc-info-value").inner_text().strip()
            long_raw = card_scope.locator(".gc-info-item", has_text="Longitude").locator(".gc-info-value").inner_text().strip()

            # 2. Fungsi Pembantu Validasi (agar kode bersih)
            def is_coord_valid(lat, lon):
                invalid_indicators = ["-", "", "0", "0.0", "undefined", "null", "none", "nan"]
                if str(lat).lower() in invalid_indicators or str(lon).lower() in invalid_indicators:
                    return False
                try:
                    float(str(lat).replace(',', '.'))
                    float(str(lon).replace(',', '.'))
                    return True
                except (ValueError, TypeError):
                    return False

            web_coord_valid = is_coord_valid(lat_raw, long_raw)

            # 3. Inisialisasi Locator Tombol
            tandai_locator = card_scope.locator(".btn-tandai")
            edit_locator = card_scope.locator(".btn-gc-edit")
            hasil_edit = False  # flag hasil edit

            
            # 4. Logika Percabangan
            if tandai_locator.count() == 0:
                # Skenario: Tombol Tandai Tidak Ada
                if web_coord_valid:
                    # KONDISI 1: Sudah valid di web, skip saja
                    # Pesan dinamis agar log tidak ambigu
                    is_gc = card_scope.locator(".gc-badge", has_text="Sudah GC").count() > 0
                    msg = f"{'Sudah GC' if is_gc else 'button tandai tidak ditemukan'}; lat/long sudah valid"
                    
                    # Tulisakan note
                    log_info(f"Skipped: {msg}.", idsbr=idsbr or "-")
                    note = msg
                    stats["skipped_gc"] += 1
                    status = "skipped"
                    continue
                else:
                    # KONDISI 2: koordinat Web invalid, cari tombol edit
                    if edit_locator.count() > 0:
                        log_info("Info: Menggunakan tombol Edit...", idsbr=idsbr or "-")
                        tandai_locator = edit_locator
                        stats["hasil_gc_invalid_coordinate"] += 1
                        hasil_edit = True  # merupakan hasil edit
                    else:
                        # KONDISI 3: Gagal total
                        log_warn("Gagal: Tombol tandai tidak ada, koordinat web invalid, & syarat edit tidak terpenuhi.", idsbr=idsbr or "-")
                        stats["skipped_no_tandai"] += 1
                        note = "button tandai tidak ditemukan; lat/long invalid; tidak bisa edit/input"
                        status = "gagal"
                        continue
            
            # Pengecekan visibilitas untuk locator yang terpilih (tandai atau edit)
            if not tandai_locator.first.is_visible():
                log_warn("Tombol aksi tidak terlihat; skipping.", idsbr=idsbr or "-")
                stats["skipped_no_tandai"] += 1
                status = "gagal"
                note = "Tombol aksi (tandai/edit) tidak terlihat"
                continue

            wait_for_block_ui_clear(page, monitor, timeout_s=15)
            try:
                tandai_locator.first.scroll_into_view_if_needed()
            except Exception:
                pass
            try:
                monitor.bot_click(tandai_locator.first)
            except Exception as exc:
                log_warn(
                    "Tombol Tandai gagal diklik; skipping.",
                    idsbr=idsbr or "-",
                    error=str(exc),
                )
                stats["skipped_no_tandai"] += 1
                status = "gagal"
                note = "Tombol Tandai gagal diklik"
                continue
            form_ready = monitor.wait_for_condition(
                lambda: page.locator("#tt_hasil_gc").count() > 0,
                timeout_s=30,
            )
            if not form_ready:
                log_warn(
                    "Form Hasil GC tidak muncul; skipping.",
                    idsbr=idsbr or "-",
                )
                stats["skipped_no_tandai"] += 1
                status = "gagal"
                note = "Form Hasil GC tidak muncul"
                continue

            if hasil_gc_select(page, monitor, hasil_gc):
                log_info(
                    "Hasil GC set.", hasil_gc=hasil_gc, idsbr=idsbr or "-"
                )
                stats["hasil_gc_set"] += 1
            else:
                log_warn(
                    "Hasil GC tidak diisi (kode tidak valid/kosong).",
                    idsbr=idsbr or "-",
                )
                stats["hasil_gc_skipped"] += 1
                status = "gagal"
                note = "Hasil GC tidak valid/kosong"

            def safe_fill(selector, value, field_name):
                locator = page.locator(selector)
                if locator.count() == 0 or not locator.first.is_visible():
                    log_warn(
                        "Field tidak ditemukan; lewati.",
                        idsbr=idsbr or "-",
                        field=field_name,
                    )
                    return
                try:
                    current_value = locator.first.input_value()
                except Exception:
                    current_value = ""
                
                # Normalisasi nilai untuk perbandingan
                current_normalized = str(current_value).strip() if current_value else ""
                new_normalized = str(value).strip() if value else ""
                
                # Skip jika nilai Excel kosong
                if not new_normalized:
                    log_info(
                        f"Skip {field_name}: nilai Excel kosong.",
                        idsbr=idsbr or "-",
                    )
                    return
                
                # Bandingkan nilai - hanya isi jika berbeda
                if current_normalized == new_normalized:
                    log_info(
                        f"Skip {field_name}: nilai sama ({current_normalized}).",
                        idsbr=idsbr or "-",
                    )
                    return
                
                # Jika current kosong atau berbeda, update
                if current_normalized:
                    log_info(
                        f"Update {field_name}: \'{current_normalized}\' -> \'{new_normalized}\'.",
                        idsbr=idsbr or "-",
                    )
                else:
                    log_info(
                        f"Fill {field_name}: \'{new_normalized}\' (sebelumnya kosong).",
                        idsbr=idsbr or "-",
                    )
                
                monitor.bot_fill(selector, value)

            safe_fill("#tt_latitude_cek_user", latitude, "latitude")
            safe_fill("#tt_longitude_cek_user", longitude, "longitude")

            if status == "gagal" and note == "Hasil GC tidak valid/kosong":
                monitor.bot_goto(TARGET_URL)
                continue

            submit_locator = page.locator("#save-tandai-usaha-btn")
            if submit_locator.count() == 0:
                log_warn(
                    "Tombol submit tidak ditemukan; skipping.",
                    idsbr=idsbr or "-",
                )
                status = "gagal"
                note = "Tombol submit tidak ditemukan"
                monitor.bot_goto(TARGET_URL)
                continue
            if not submit_locator.first.is_visible():
                log_warn(
                    "Tombol submit tidak terlihat; skipping.",
                    idsbr=idsbr or "-",
                )
                status = "gagal"
                note = "Tombol submit tidak terlihat"
                monitor.bot_goto(TARGET_URL)
                continue

            wait_for_block_ui_clear(page, monitor, timeout_s=15)
            try:
                submit_locator.first.scroll_into_view_if_needed()
            except Exception:
                pass
            try:
                monitor.bot_click(submit_locator.first)
            except Exception as exc:
                log_warn(
                    "Tombol submit gagal diklik; skipping.",
                    idsbr=idsbr or "-",
                    error=str(exc),
                )
                status = "gagal"
                note = "Tombol submit gagal diklik"
                monitor.bot_goto(TARGET_URL)
                continue

            confirm_text = "tanpa melakukan geotag"
            success_text = "Data submitted successfully"
            swal_result = None

            def find_swal():
                nonlocal swal_result
                confirm_popup = page.locator(
                    ".swal2-popup", has_text=confirm_text
                )
                if (
                    confirm_popup.count() > 0
                    and confirm_popup.first.is_visible()
                ):
                    swal_result = "confirm"
                    return True
                success_popup = page.locator(
                    ".swal2-popup", has_text=success_text
                )
                if (
                    success_popup.count() > 0
                    and success_popup.first.is_visible()
                ):
                    swal_result = "success"
                    return True
                return False

            monitor.wait_for_condition(find_swal, timeout_s=15)

            if swal_result == "confirm":
                if not latitude and not longitude:
                    confirm_popup = page.locator(
                        ".swal2-popup", has_text=confirm_text
                    )
                    confirm_button = confirm_popup.locator(
                        ".swal2-confirm", has_text="Ya"
                    )
                    if confirm_button.count() > 0:
                        monitor.bot_click(confirm_button.first)
                    else:
                        log_warn(
                            "Tombol Ya pada dialog geotag tidak ditemukan.",
                            idsbr=idsbr or "-",
                        )
                        status = "gagal"
                        note = "Dialog geotag tanpa tombol Ya"
                        monitor.bot_goto(TARGET_URL)
                        continue
                else:
                    log_warn(
                        "Dialog geotag muncul padahal koordinat ada.",
                        idsbr=idsbr or "-",
                    )
                    status = "gagal"
                    note = "Anomali dialog geotag"
                    monitor.bot_goto(TARGET_URL)
                    continue

            if swal_result != "success":
                swal_result = None

                def find_success():
                    nonlocal swal_result
                    success_popup = page.locator(
                        ".swal2-popup", has_text=success_text
                    )
                    if (
                        success_popup.count() > 0
                        and success_popup.first.is_visible()
                    ):
                        swal_result = "success"
                        return True
                    return False

                if not monitor.wait_for_condition(find_success, timeout_s=15):
                    log_warn(
                        "Dialog sukses submit tidak muncul; skipping.",
                        idsbr=idsbr or "-",
                    )
                    status = "gagal"
                    note = "Dialog sukses tidak muncul"
                    monitor.bot_goto(TARGET_URL)
                    continue

            success_popup = page.locator(
                ".swal2-popup", has_text=success_text
            )
            ok_button = success_popup.locator(
                ".swal2-confirm", has_text="OK"
            )
            if ok_button.count() == 0:
                log_warn(
                    "Tombol OK pada dialog sukses tidak ditemukan.",
                    idsbr=idsbr or "-",
                )
                status = "gagal"
                note = "Dialog sukses tanpa tombol OK"
                monitor.bot_goto(TARGET_URL)
                continue
            monitor.bot_click(ok_button.first)
            monitor.wait_for_condition(
                lambda: page.locator(".swal2-popup").count() == 0
                or not page.locator(".swal2-popup").first.is_visible(),
                timeout_s=10,
            )
            monitor.wait_for_condition(
                lambda: is_visible(page, "#search-idsbr")
                or page.locator(".usaha-card-header").count() > 0,
                timeout_s=10,
            )
            if not page.url.startswith(TARGET_URL):
                monitor.bot_goto(TARGET_URL)
            status = "berhasil"
            note = "Submit sukses"
        except Exception as exc:
            log_error(
                "Error while processing row.",
                idsbr=idsbr or "-",
                error=str(exc),
            )
            status = "error"
            note = str(exc)
        finally:
            # Update note SEBELUM append
            if (status or "error") == "berhasil" and hasil_edit:
                note = f"{note}; Update via Edit".strip("; ")
                stats["hasil_gc_edited"] += 1
            
            run_log_rows.append(
                {
                    "no": excel_row,
                    "idsbr": idsbr or "",
                    "nama_usaha": nama_usaha or "",
                    "alamat": alamat or "",
                    "keberadaanusaha_gc": hasil_gc if hasil_gc is not None else "",
                    "latitude": latitude or "",
                    "longitude": longitude or "",
                    "status": status or "error",
                    "catatan": note,
                }
            )
            summary_status = status or "error"
            summary_note = note or "-"
            summary_fields = {
                "row": batch_index,
                "row_excel": excel_row,
                "idsbr": idsbr or "-",
                "status": summary_status,
                "note": summary_note,
            }
            if summary_status == "berhasil":
                log_info("Row summary.", **summary_fields)
            elif summary_status in {"gagal", "skipped"}:
                log_warn("Row summary.", **summary_fields)
            else:
                log_error("Row summary.", **summary_fields)
            if progress_callback:
                try:
                    progress_callback(
                        stats["processed"],
                        selected_rows,
                        excel_row,
                    )
                except Exception:
                    pass


    # PATCH Logging
    # 1. Log Ringkasan ke Terminal
    log_info("Processing completed.", _spacer=True, _divider=True)
    log_info(
        "Summary Details:",
        Berhasil_Murni=stats["hasil_gc_set"],
        Berhasil_Via_Edit=stats["hasil_gc_edited"],
        Skip_Sudah_GC=stats["skipped_gc"],
        Skip_Koordinat_Invalid=stats["hasil_gc_invalid_coordinate"],
        Skip_Duplikat=stats["skipped_duplikat"],
        Total_Processed=stats["processed"]
    )

    # 2. Simpan Log
    write_run_log(run_log_rows, run_log_path, stats=stats)
    log_info("Run log & Summary sheet saved.", path=str(run_log_path))