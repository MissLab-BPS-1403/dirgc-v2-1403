#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Add warning handler logic after the existing warning detection"""

with open('dirgc/browser.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the position after "monitor.wait_for_condition(find_swal, timeout_s=30)"
target = "    monitor.wait_for_condition(find_swal, timeout_s=30)\n    \n    if swal_result == \"success\":"

if target in content:
    # Add the warning handler before "if swal_result == \"success\":"
    new_code = '''    monitor.wait_for_condition(find_swal, timeout_s=30)
    
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
    if swal_result == "success":'''
    
    content = content.replace(target, new_code)
    
    with open('dirgc/browser.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("File updated successfully!")
else:
    print("Target section not found!")
