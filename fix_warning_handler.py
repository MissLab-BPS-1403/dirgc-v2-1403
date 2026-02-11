#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fix warning handler in browser.py"""

with open('dirgc/browser.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the line with "Clicking Simpan."
new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    
    # Look for the start of the section to replace
    if 'log_info("Clicking Simpan.")' in line:
        # Replace the entire section from here
        # First, add everything before this line
        new_lines.append(line.replace('Clicking Simpan.', 'Clicking Simpan (pertama kali).'))
        i += 1
        
        # Add the next lines until bot_click
        while i < len(lines) and 'monitor.bot_click(simpan.first)' not in lines[i]:
            new_lines.append(lines[i])
            i += 1
        
        # Add monitor.bot_click
        if i < len(lines):
            new_lines.append(lines[i])
            i += 1
        
        # Skip the exception handler
        while i < len(lines) and 'return False' not in lines[i]:
            new_lines.append(lines[i])
            i += 1
        
        if i < len(lines):
            new_lines.append(lines[i])  # return False
            i += 1
            
        # Now add new code - wait for popup
        new_lines.append('    \n')
        new_lines.append('    # Tunggu popup muncul\n')
        new_lines.append('    page.wait_for_timeout(2000)\n')
        new_lines.append('    \n')
        
        # Now skip all old code until we find the final "return False" of the function
        # We're looking for the section that starts with "swal_result = None"
        while i < len(lines) and 'swal_result = None' not in lines[i]:
            i += 1
        
        # Skip the old handling code
        skip_count = 0
        found_end = False
        while i < len(lines):
            line_content = lines[i]
            
            # Look for three consecutive "return False" which marks end of function
            if 'monitor.bot_goto(TARGET_URL)' in line_content and i + 1 < len(lines) and 'return False' in lines[i+1]:
                # This is one of the final returns - skip it
                new_lines.append(lines[i])
                new_lines.append(lines[i+1])
                i += 2
                
                # Check if this is truly the end (next lines are blank or new function)
                if i < len(lines) and (lines[i].strip() == '' or not lines[i].startswith(' ')):
                    found_end = True
                    break
            else:
                i += 1
        
        # Now insert the new code before the last section
        new_code = '''    swal_result = None
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
    
    # CASE 3: Duplicate
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
    
    # CASE 4: Error/timeout
    else:
        log_warn("Submit failed/timeout.")
        monitor.bot_goto(TARGET_URL)
        return False
'''
        
        # Remove the last 2 lines that were already added
        new_lines = new_lines[:-2]
        new_lines.append(new_code)
        new_lines.append('\n')
        new_lines.append('\n')
        
        # Continue with the rest of the file
        continue
    
    new_lines.append(line)
    i += 1

# Write the modified content
with open('dirgc/browser.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("File fixed successfully!")
