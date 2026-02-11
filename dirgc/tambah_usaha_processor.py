from .browser import (
    add_usaha,
    ensure_on_dirgc,
)
from .logging_utils import log_error, log_info, log_warn
from .run_logs import build_run_log_path, write_run_log
from .tambah_usaha_excel import load_tambah_usaha_rows


def process_tambah_usaha_rows(
    page,
    monitor,
    excel_file,
    use_saved_credentials,
    credentials,
    start_row=None,
    end_row=None,
    progress_callback=None,
):
    """
    Process rows for Tambah Usaha Baru (mode khusus tanpa filter/matching)
    Langsung tambah usaha baru dari Excel
    """
    run_log_path = build_run_log_path(prefix="tambah_usaha")
    run_log_rows = []
    
    try:
        rows = load_tambah_usaha_rows(excel_file)
    except Exception as exc:
        log_error("Failed to load Excel file for Tambah Usaha.")
        run_log_rows.append(
            {
                "no": 0,
                "idsbr": "",
                "nama_usaha": "",
                "alamat": "",
                "provinsi": "",
                "kabupaten": "",
                "kecamatan": "",
                "kelurahan": "",
                "keberadaanusaha_gc": "2",
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
        "berhasil": 0,
        "gagal": 0,
        "duplikasi": 0,
    }
    
    log_info(
        "Start processing Tambah Usaha rows.",
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

        nama_usaha = row["nama_usaha"]
        alamat = row["alamat"]
        provinsi = row.get("provinsi", "")
        kabupaten = row.get("kabupaten", "")
        kecamatan = row.get("kecamatan", "")
        kelurahan = row.get("kelurahan", "")
        latitude = row["latitude"]
        longitude = row["longitude"]

        log_info(
            "Processing Tambah Usaha row.",
            _spacer=True,
            _divider=True,
            row=batch_index,
            total=selected_rows,
            row_excel=excel_row,
            nama_usaha=nama_usaha or "-",
            alamat=alamat or "-",
            provinsi=provinsi or "-",
            kabupaten=kabupaten or "-",
            kecamatan=kecamatan or "-",
            kelurahan=kelurahan or "-",
        )
        
        ensure_on_dirgc(
            page,
            monitor=monitor,
            use_saved_credentials=use_saved_credentials,
            credentials=credentials,
        )

        try:
            log_info(
                "Adding new usaha.",
                nama_usaha=nama_usaha or "-",
                alamat=alamat or "-",
                provinsi=provinsi or "-",
                kabupaten=kabupaten or "-",
                kecamatan=kecamatan or "-",
                kelurahan=kelurahan or "-",
                latitude=latitude or "-",
                longitude=longitude or "-",
            )
            
            # Tambah usaha baru (sudah ada cek duplikasi di dalam)
            result = add_usaha(
                page,
                monitor,
                idsbr="",
                nama_usaha=nama_usaha,
                alamat=alamat,
                provinsi=provinsi,
                kabupaten=kabupaten,
                kecamatan=kecamatan,
                kelurahan=kelurahan,
                latitude=latitude,
                longitude=longitude,
            )
            
            if result is True:
                log_info("Usaha added successfully.", nama_usaha=nama_usaha or "-")
                status = "berhasil"
                note = "Tambah usaha sukses"
                stats["berhasil"] += 1
            elif result is False:
                # Bisa karena duplikasi atau error lainnya
                # Cek dari log terakhir
                log_warn("Failed to add usaha.", nama_usaha=nama_usaha or "-")
                status = "gagal"
                note = "Tambah usaha gagal atau duplikasi"
                stats["gagal"] += 1
            else:
                status = "gagal"
                note = "Unknown result"
                stats["gagal"] += 1

        except Exception as exc:
            log_error(
                "Error while processing row.",
                nama_usaha=nama_usaha or "-",
                error=str(exc),
            )
            status = "error"
            note = str(exc)
            stats["gagal"] += 1
        
        finally:
            run_log_rows.append(
                {
                    "no": excel_row,
                    "idsbr": "",
                    "nama_usaha": nama_usaha or "",
                    "alamat": alamat or "",
                    "provinsi": provinsi or "",
                    "kabupaten": kabupaten or "",
                    "kecamatan": kecamatan or "",
                    "kelurahan": kelurahan or "",
                    "keberadaanusaha_gc": "2",
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
                "nama_usaha": nama_usaha or "-",
                "provinsi": provinsi or "-",
                "kabupaten": kabupaten or "-",
                "kecamatan": kecamatan or "-",
                "kelurahan": kelurahan or "-",
                "status": summary_status,
                "note": summary_note,
            }
            
            if summary_status == "berhasil":
                log_info("Row summary.", **summary_fields)
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

    log_info("Processing completed.", _spacer=True, _divider=True, **stats)
    write_run_log(run_log_rows, run_log_path)
    log_info("Run log saved.", path=str(run_log_path))
