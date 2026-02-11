import re
from datetime import datetime
from pathlib import Path


LOGS_DIR = "logs"


def _next_run_number(date_dir):
    max_run = 0
    for path in date_dir.glob("run*_*.xlsx"):
        match = re.match(r"run(\d+)_", path.stem)
        if not match:
            continue
        try:
            number = int(match.group(1))
        except ValueError:
            continue
        if number > max_run:
            max_run = number
    return max_run + 1


def build_run_log_path(now=None, prefix=None):
    now = now or datetime.now()
    date_folder = now.strftime("%Y%m%d")
    date_dir = Path(LOGS_DIR) / date_folder
    date_dir.mkdir(parents=True, exist_ok=True)
    run_number = _next_run_number(date_dir)
    time_label = now.strftime("%H%M")
    if prefix:
        filename = f"{prefix}_run{run_number}_{time_label}.xlsx"
    else:
        filename = f"run{run_number}_{time_label}.xlsx"
    return date_dir / filename


def write_run_log(rows, output_path, stats=None):
    columns = [
        "no",
        "idsbr",
        "nama_usaha",
        "alamat",
        "provinsi",
        "kabupaten",
        "kecamatan",
        "kelurahan",
        "keberadaanusaha_gc",
        "latitude",
        "longitude",
        "status",
        "catatan",
    ]

    try:
        import pandas as pd
    except ImportError:
        pd = None

    if pd:
        df = pd.DataFrame(rows, columns=columns)
        df.to_excel(output_path, index=False)
        return

    try:
        import openpyxl
    except ImportError as exc:
        raise RuntimeError(
            "Install pandas or openpyxl to write log Excel."
        ) from exc

    workbook = openpyxl.Workbook()
    
    # Sheet 1
    sheet1 = workbook.active
    sheet1.title = "Run_Log"
    sheet1.append(columns)
    for row in rows:
        sheet1.append([row.get(col, "") for col in columns])
    
    # Sheet 2
    if stats:
        sheet2 = workbook.create_sheet(title="Summary")
        stats_keys = list(stats.keys())
        sheet2.append(stats_keys)
        sheet2.append([stats.get(k) for k in stats_keys])
        
    workbook.save(output_path)
    workbook.close()