#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Update safe_fill function untuk conditional replace"""

with open('dirgc/processor.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Find and replace safe_fill function
old_func = '''            def safe_fill(selector, value, field_name):
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
                if current_value and str(current_value).strip():
                    return
                if not value:
                    return
                monitor.bot_fill(selector, value)'''

new_func = '''            def safe_fill(selector, value, field_name):
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
                        f"Update {field_name}: \\'{current_normalized}\\' -> \\'{new_normalized}\\'.",
                        idsbr=idsbr or "-",
                    )
                else:
                    log_info(
                        f"Fill {field_name}: \\'{new_normalized}\\' (sebelumnya kosong).",
                        idsbr=idsbr or "-",
                    )
                
                monitor.bot_fill(selector, value)'''

if old_func in content:
    content = content.replace(old_func, new_func)
    with open('dirgc/processor.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print('Updated successfully!')
else:
    print('Pattern not found!')
