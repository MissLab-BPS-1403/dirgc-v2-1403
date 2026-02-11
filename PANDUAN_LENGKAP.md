# Panduan Lengkap Instalasi & Penggunaan
## Otomatisasi MatchaPro - Ground Check & Tambah Usaha Baru

---

## 📋 Daftar Isi

1. [Persiapan Awal](#1-persiapan-awal)
2. [Install Python](#2-install-python)
3. [Download Project](#3-download-project)
4. [Install Dependencies](#4-install-dependencies)
5. [Konfigurasi Akun](#5-konfigurasi-akun)
6. [Persiapan File Excel](#6-persiapan-file-excel)
7. [Menjalankan Aplikasi](#7-menjalankan-aplikasi)
8. [Troubleshooting](#8-troubleshooting)
9. [Transfer ke Komputer Lain](#9-transfer-ke-komputer-lain)

---

## 1. Persiapan Awal

### Yang Dibutuhkan:
- ✅ Komputer dengan Windows 10/11
- ✅ Koneksi internet (untuk download Python & dependencies)
- ✅ Akun MatchaPro (username & password SSO)
- ✅ File Excel dengan data yang akan diproses
- ✅ Minimal 500 MB ruang disk kosong

---

## 2. Install Python

### Langkah 2.1: Download Python

1. Buka browser, kunjungi: **https://www.python.org/downloads/**
2. Klik tombol **"Download Python 3.x.x"** (versi terbaru)
3. Tunggu hingga file installer selesai didownload

### Langkah 2.2: Install Python

1. **Double-click** file installer yang sudah didownload (contoh: `python-3.12.1-amd64.exe`)

2. **PENTING!** Di layar pertama:
   - ☑️ **Centang** "Add python.exe to PATH" (WAJIB!)
   - Klik **"Install Now"**

   ```
   ┌────────────────────────────────────┐
   │  Install Python 3.12.1             │
   │                                    │
   │  ☑ Add python.exe to PATH  ←─── CENTANG INI!
   │                                    │
   │  [Install Now]                     │
   └────────────────────────────────────┘
   ```

3. Tunggu proses instalasi selesai
4. Klik **"Close"**

### Langkah 2.3: Verifikasi Instalasi

1. Buka **Command Prompt**:
   - Tekan `Windows + R`
   - Ketik `cmd`
   - Tekan `Enter`

2. Ketik perintah berikut dan tekan Enter:
   ```cmd
   python --version
   ```

3. Jika berhasil, akan muncul:
   ```
   Python 3.12.1
   ```

4. Cek pip juga:
   ```cmd
   pip --version
   ```
   
   Seharusnya muncul:
   ```
   pip 23.x.x from ...
   ```

✅ **Jika kedua perintah di atas berhasil, Python sudah terinstall dengan benar!**

❌ **Jika muncul error "python is not recognized":**
   - Python belum masuk PATH
   - Ulangi instalasi, pastikan centang "Add python.exe to PATH"

---

## 3. Mendapatkan Project

### Copy Project dari USB/Flashdisk atau File ZIP

1. **Dapatkan folder project:**
   - Dari USB/flashdisk yang sudah berisi folder automasimatcha
   - Atau dari file ZIP yang diterima

2. **Copy ke komputer:**
   - Paste/Extract folder ke lokasi yang diinginkan
   - Contoh lokasi: D:\Projectsutomasimatcha
   
3. **Pastikan struktur folder lengkap:**
   `
   automasimatcha/
   ├── dirgc/
   ├── config/
   ├── data/
   ├── logs/
   ├── run_matcha_gui.py
   ├── requirements.txt
   └── ...
   `

4. **Buka Command Prompt di folder project:**
   `cmd
   D:
   cd Projectsutomasimatcha
   `

**Tips:** Untuk memastikan sudah berada di folder yang benar, ketik dir dan pastikan ada file run_matcha_gui.py dan requirements.txt

---

## 4. Install Dependencies

### Langkah 4.1: Install Python Libraries

Masih di Command Prompt (sudah berada di folder project):

```cmd
pip install -r requirements.txt
```

Proses ini akan:
- Download & install: playwright, pandas, openpyxl, PyQt5, PyQt-Fluent-Widgets
- Membutuhkan waktu 2-5 menit (tergantung koneksi internet)

**Tunggu hingga muncul:**
```
Successfully installed playwright-x.x.x pandas-x.x.x openpyxl-x.x.x ...
```

### Langkah 4.2: Install Browser Chromium

Setelah library terinstall, install browser untuk Playwright:

```cmd
playwright install chromium
```

**Tunggu hingga selesai** (download ~100-150 MB):
```
Downloading Chromium ...
Chromium x.x.x downloaded to ...
```

✅ **Instalasi selesai!** Project siap digunakan.

---

## 5. Konfigurasi Akun

Ada 2 cara: Melalui GUI atau File

### Cara 5A: Melalui GUI (Paling Mudah)

1. Jalankan aplikasi (lihat bagian 7)
2. Klik menu **"Akun SSO"** di aplikasi
3. Isi:
   - Username: `username_sso_anda`
   - Password: `password_sso_anda`
4. Klik **"Simpan"**

**Catatan:** Kredensial hanya tersimpan selama aplikasi berjalan (tidak disimpan ke file).

### Cara 5B: Melalui File (Auto-Login Permanen)

1. Buka folder `config` di project
2. Buat file baru bernama `credentials.json`
3. Isi dengan format berikut:

```json
{
  "username": "username_sso_anda",
  "password": "password_sso_anda"
}
```

**Contoh:**
```json
{
  "username": "211709876",
  "password": "rahasia123"
}
```

4. Simpan file

**Keamanan:**
- ⚠️ File ini berisi password plaintext
- Jangan share ke orang lain
- Di komputer pribadi: aman
- Di komputer kantor/shared: gunakan cara 5A saja

---

## 6. Persiapan File Excel

### Format Excel untuk Update Usaha (DIRGC)

Buat/siapkan file Excel dengan kolom berikut:

| idsbr | nama_usaha | alamat | hasil_gc | latitude | longitude |
|-------|-----------|--------|----------|----------|-----------|
| 1234567890 | Toko ABC | Jl. Merdeka No. 1 | 1 | -0.123456 | 117.123456 |
| 2345678901 | Warung XYZ | Jl. Sudirman No. 2 | 1 | -0.234567 | 117.234567 |

**Keterangan Kolom:**
- `idsbr`: ID usaha (wajib)
- `nama_usaha`: Nama usaha
- `alamat`: Alamat usaha
- `hasil_gc`: Kode hasil GC
  - `0` = Tidak Ditemukan
  - `1` = Ditemukan ✅ (paling sering)
  - `2` = Tambah Usaha Baru
  - `3` = Tutup
  - `4` = Ganda
- `latitude`: Koordinat lintang (format desimal, bisa kosong)
- `longitude`: Koordinat bujur (format desimal, bisa kosong)

**Simpan file ke folder `data/`** di project (contoh: `data/data_gc.xlsx`)

### Format Excel untuk Tambah Usaha Baru

Buat file Excel dengan kolom berikut:

| nama_usaha | alamat | provinsi | kabupaten | kecamatan | kelurahan | latitude | longitude |
|-----------|--------|----------|-----------|-----------|-----------|----------|-----------|
| AMPERA AJO | Jl. A. Yani | Riau | Pekanbaru | Senapelan | Padang Bulan | 0.5304034 | 101.4425177 |
| TOKO BARU | Jl. Sudirman | Riau | Pekanbaru | Sukajadi | Kampung Baru | 0.5123456 | 101.4234567 |

**PENTING untuk Nama Wilayah:**
- ⚠️ Harus **persis sama** dengan nama di aplikasi MatchaPro
- Huruf besar/kecil harus sama
- Tidak boleh ada spasi ekstra
- **Tip:** Copy-paste langsung dari aplikasi

**Simpan file** (contoh: `tambah_usaha.xlsx`) di mana saja, nanti pilih lewat GUI.

---

## 7. Menjalankan Aplikasi

### Cara 7A: Jalankan GUI (Recommended)

1. Buka Command Prompt di folder project:
   ```cmd
   D:
   cd Projects\automasimatcha
   ```

2. Jalankan GUI:
   ```cmd
   python run_matcha_gui.py
   ```

3. **Aplikasi akan terbuka** dengan tampilan modern

### Menggunakan Fitur Update Usaha:

1. Di aplikasi, pilih tab/menu **"Update Usaha"**
2. Klik **"Pilih File Excel"**, pilih file Excel Anda
3. (Opsional) Atur **Start Row** dan **End Row**
   - Contoh: Start=1, End=10 → proses baris 1-10 saja
   - Kosongkan untuk proses semua baris
4. Klik **"Mulai Proses"**
5. Browser akan terbuka otomatis
6. **Jika login manual:**
   - Login ke SSO seperti biasa
   - Masukkan OTP jika diminta
   - Aplikasi akan lanjut otomatis setelah login berhasil
7. Pantau progress di aplikasi

### Menggunakan Fitur Tambah Usaha Baru:

1. Di aplikasi, pilih tab/menu **"Tambah Usaha Baru"**
2. Klik **"Pilih File Excel"**, pilih file Excel tambah usaha
3. (Opsional) Atur Start/End Row
4. Klik **"Mulai Proses"**
5. Browser akan terbuka, proses berjalan otomatis

### Cara 7B: Jalankan CLI (Advanced)

**Update Usaha:**
```cmd
python run_dirgc.py --excel-file data/data_gc.xlsx --start 1 --end 10
```

**Tambah Usaha Baru:**
```cmd
python run_tambah_usaha.py
```

---

## 8. Troubleshooting

### Problem: "python is not recognized"

**Penyebab:** Python tidak ada di PATH

**Solusi:**
1. Uninstall Python (Control Panel → Uninstall a program)
2. Install ulang, **PASTIKAN centang "Add python.exe to PATH"**
3. Restart Command Prompt

### Problem: "pip is not recognized"

**Solusi:**
Gunakan format lengkap:
```cmd
python -m pip install -r requirements.txt
```

### Problem: Error saat `pip install -r requirements.txt`

**Penyebab:** Koneksi internet bermasalah atau butuh upgrade pip

**Solusi:**
```cmd
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Problem: Error saat `playwright install chromium`

**Solusi:**
```cmd
playwright install --force chromium
```

### Problem: Browser tidak muncul

**Penyebab:** Mode headless aktif

**Solusi:**
- Pastikan tidak ada flag `--headless`
- Cek antivirus/firewall, pastikan tidak memblokir browser

### Problem: Koordinat tidak ter-update

**Kemungkinan:**

1. **Nilai sama** → Sistem skip (ini normal)
   - Log: "Skip latitude: nilai sama (0.123456)"
   
2. **Excel kosong** → Sistem skip (ini normal)
   - Log: "Skip latitude: nilai Excel kosong"

3. **Field tidak terlihat** → Error
   - Log: "Field tidak ditemukan; lewati"
   - Solusi: Scroll manual atau laporkan bug

### Problem: Nama wilayah tidak ditemukan (Tambah Usaha)

**Penyebab:** Nama tidak sesuai dengan di aplikasi

**Solusi:**
1. Buka MatchaPro manual
2. Buka form "Tambah Usaha Baru"
3. Klik dropdown Provinsi/Kabupaten/dll
4. **Copy persis** nama yang muncul di dropdown
5. Paste ke Excel
6. Pastikan huruf besar/kecil sama

**Contoh Salah vs Benar:**
- ❌ `pekanbaru` 
- ❌ `PEKANBARU`
- ✅ `Pekanbaru`

### Problem: Warning popup tidak hilang

**Solusi:**
Sistem sudah otomatis handle:
1. Klik OK
2. Scroll ke bawah
3. Centang checkbox
4. Klik Simpan lagi

Jika masih error, laporkan dengan screenshot.

### Problem: "Timeout" error

**Penyebab:** Loading lambat atau internet bermasalah

**Solusi:**
```cmd
# Tingkatkan timeout
python run_matcha_gui.py --web-timeout-s 60
```

Atau di GUI: Settings → Web Timeout → set 60

---

## 9. Transfer ke Komputer Lain

### Persiapan di Komputer Sumber

1. **Copy folder project:**
   - Copy seluruh folder `automasimatcha`
   - Pastikan struktur lengkap

2. **File yang perlu di-copy:**
   - ✅ Seluruh folder project
   - ✅ `requirements.txt` (wajib)
   - ✅ File Excel di `data/` (jika ada)
   - ⚠️ `config/credentials.json` (opsional, berisi password)

3. **File yang TIDAK perlu:**
   - ❌ Folder `__pycache__/`
   - ❌ Folder `logs/` (kecuali mau backup log)
   - ❌ File `.pyc`

### Instalasi di Komputer Tujuan

#### Langkah 1: Install Python (jika belum ada)

Ikuti **[Bagian 2](#2-install-python)** di panduan ini.

#### Langkah 2: Copy Project

1. Paste folder `automasimatcha` ke komputer baru
2. Contoh lokasi: `D:\Projects\automasimatcha`

#### Langkah 3: Install Dependencies

```cmd
# Masuk ke folder project
D:
cd Projects\automasimatcha

# Install dependencies
pip install -r requirements.txt

# Install browser
playwright install chromium
```

#### Langkah 4: Konfigurasi Akun (jika perlu)

Jika tidak copy `credentials.json`:
- Buat file baru sesuai **[Bagian 5B](#cara-5b-melalui-file-auto-login-permanen)**
- Atau isi lewat GUI sesuai **[Bagian 5A](#cara-5a-melalui-gui-paling-mudah)**

#### Langkah 5: Test Run

```cmd
python run_matcha_gui.py
```

✅ **Selesai!** Aplikasi siap digunakan di komputer baru.

---

## 10. Tips & Best Practices

### Untuk Pemula:

1. **Mulai dengan data kecil:**
   - Test dengan 5-10 baris dulu
   - Cek hasilnya di log
   - Baru proses data lengkap

2. **Backup data Excel:**
   - Selalu simpan copy original
   - Gunakan copy untuk testing

3. **Pantau log terminal:**
   - Baca pesan error/warning
   - Screenshoot jika ada masalah

4. **Jangan tutup browser:**
   - Browser akan otomatis tertutup setelah selesai
   - Tutup manual = proses gagal

### Untuk Power User:

1. **Gunakan range row:**
   ```cmd
   python run_dirgc.py --start 1 --end 100
   ```

2. **Parallel processing:**
   - Jalankan 2 instance dengan range berbeda
   - Misal: Instance 1 (row 1-500), Instance 2 (row 501-1000)

3. **Custom timeout:**
   ```cmd
   python run_dirgc.py --idle-timeout-ms 600000 --web-timeout-s 60
   ```

4. **Background mode (tidak recommended untuk SSO):**
   ```cmd
   python run_dirgc.py --headless
   ```

---

## 11. Cara Membaca Log

### Log di Terminal

**Format:**
```
[HH:MM:SS] LEVEL: Message | key=value | key2=value2
```

**Contoh:**
```
[14:30:15] INFO: Processing row. | row=1 | idsbr=1234567890
[14:30:18] INFO: Skip latitude: nilai sama (0.123456). | idsbr=1234567890
[14:30:19] INFO: Update longitude: '117.111111' -> '117.222222'. | idsbr=1234567890
[14:30:25] INFO: Row summary. | row=1 | status=berhasil | note="Submit sukses"
```

**Status yang mungkin:**
- ✅ `berhasil` - Data berhasil diupdate
- ⚠️ `skipped` - Data sudah GC/duplikat (normal)
- ❌ `gagal` - Ada error (cek catatan)
- ❌ `error` - Error fatal

### Log File Excel

File: `logs/YYYYMMDD/run1_1430.xlsx`

**Kolom:**
- `status`: berhasil / gagal / skipped / error
- `catatan`: Detail keterangan
  - "Submit sukses"
  - "Sudah GC"
  - "Duplikat"
  - "No results found"
  - dst.

**Filter di Excel:**
- Hanya lihat yang `gagal`: Filter kolom `status` = gagal
- Hanya lihat yang `berhasil`: Filter kolom `status` = berhasil

---

## 12. FAQ (Frequently Asked Questions)

### Q: Apakah harus terkoneksi internet?

**A:** Ya, untuk:
- Install dependencies (sekali)
- Akses aplikasi MatchaPro (setiap kali pakai)

### Q: Apakah bisa tanpa login SSO?

**A:** Tidak bisa. SSO adalah satu-satunya cara login ke MatchaPro.

### Q: Apakah aman menyimpan password di `credentials.json`?

**A:** 
- Di komputer pribadi: Relatif aman
- Di komputer shared: Tidak disarankan, gunakan GUI saja
- File JSON tidak terenkripsi (plaintext)

### Q: Berapa lama proses 1000 data?

**A:** Tergantung:
- 1 data ~10-30 detik
- 1000 data ~3-8 jam
- Gunakan range untuk batch kecil

### Q: Apakah bisa proses sambil pakai komputer untuk kerja lain?

**A:** Bisa, tapi:
- Jangan minimize browser
- Jangan klik di dalam browser
- Boleh pakai aplikasi lain

### Q: Jika proses terhenti di tengah jalan?

**A:** 
1. Cek log Excel terakhir
2. Lihat baris terakhir yang berhasil
3. Lanjutkan dari baris berikutnya dengan `--start`

**Contoh:**
```cmd
# Terakhir berhasil baris 150
python run_dirgc.py --start 151 --end 1000
```

### Q: Apakah harus pakai Excel? Bisa CSV?

**A:** Harus Excel (.xlsx). Jika punya CSV:
1. Buka di Excel/LibreOffice
2. Save As → Excel Workbook (.xlsx)

### Q: Koordinat format apa yang benar?

**A:** Format desimal (Decimal Degrees):
- ✅ `-0.123456` (bisa negatif)
- ✅ `117.654321`
- ❌ `0° 7' 24.44" S` (DMS, tidak didukung)

Convert DMS ke Decimal: Gunakan tool online atau Excel formula.

---

## 13. Kontak & Dukungan

**Dikembangkan oleh:**
Tim IPDS BPS Kabupaten Bulungan

**Untuk pertanyaan/bug report:**
- GitHub Issues: https://github.com/bpskabbulungan/otomatisasidirgc-6502/issues
- Email: (jika ada)

**Update & Changelog:**
- Cek GitHub repository untuk versi terbaru

---

## 14. Lisensi & Disclaimer

- Aplikasi ini untuk internal BPS
- Gunakan dengan bijak dan bertanggung jawab
- Developer tidak bertanggung jawab atas kesalahan data hasil otomasi
- **Selalu cek hasil akhir** sebelum submit resmi

---

🎉 **Selamat! Panduan lengkap selesai.**

Jika mengikuti panduan dari awal, aplikasi seharusnya sudah berjalan dengan baik.

**Semoga membantu dan mempermudah pekerjaan! 🚀**
