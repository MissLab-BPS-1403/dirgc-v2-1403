# Otomatisasi MatchaPro - Ground Check & Tambah Usaha Baru

## Ringkasan

Aplikasi otomatisasi berbasis Playwright untuk membantu:
1. **Update Usaha (DIRGC)**: Mengisi Hasil GC dan koordinat dari data Excel
2. **Tambah Usaha Baru**: Menambahkan usaha baru dengan data lengkap (provinsi, kabupaten, kecamatan, kelurahan, koordinat)

Dilengkapi GUI berbasis PyQt5 + QFluentWidgets untuk kemudahan penggunaan.

## Instalasi di Komputer Baru

### Langkah 1: Copy Project

**Opsi A - Dari GitHub (Recommended):**
```bash
git clone https://github.com/bpskabbulungan/otomatisasidirgc-6502.git
cd otomatisasidirgc-6502
```

**Opsi B - Copy Manual:**
1. Copy seluruh folder project ke komputer baru
2. Pastikan struktur folder tetap sama
3. Buka Command Prompt/Terminal di folder project

### Langkah 2: Install Python Dependencies

```bash
# Install semua dependencies
pip install -r requirements.txt

# Install browser Chromium untuk Playwright (wajib, sekali saja)
playwright install chromium
```

**Catatan**: Jika `pip` tidak dikenali, gunakan `python -m pip` atau `python3 -m pip`

### Langkah 3: Siap Digunakan!

```bash
# Jalankan GUI
python run_matcha_gui.py
```

## File yang Perlu Di-copy

### Wajib:
- Seluruh folder project
- File `requirements.txt`

### Opsional:
- `config/credentials.json` (untuk auto-login, bisa diisi ulang di GUI)
- File Excel di `data/` (jika ada)

### Tidak Perlu:
- Folder `__pycache__/` (dibuat otomatis)
- Folder `logs/` (kecuali mau backup log lama)

## Fitur Utama

### Update Usaha (DIRGC)
- Filter usaha berdasarkan IDSBR/nama/alamat
- Update Hasil GC (0=Tidak Ditemukan, 1=Ditemukan, 2=Tambah Baru, 3=Tutup, 4=Ganda)
- **Conditional Update Koordinat**:
  - Hanya update jika nilai berbeda
  - Skip jika Excel kosong
  - Isi jika aplikasi kosong
- Auto-skip data yang sudah GC atau duplikat

### Tambah Usaha Baru
- Input data lengkap dengan wilayah administratif
- Auto-handling warning popup (klik OK, scroll, centang checkbox, simpan lagi)
- Deteksi duplikasi otomatis
- Validasi nama wilayah dengan dropdown aplikasi

## Format File Excel

### Untuk Update Usaha

Kolom yang diperlukan:
- `idsbr` - ID usaha
- `nama_usaha` - Nama usaha
- `alamat` - Alamat
- `hasil_gc` - Kode hasil GC (0-4)
- `latitude` - Koordinat latitude (opsional)
- `longitude` - Koordinat longitude (opsional)

### Untuk Tambah Usaha Baru

Kolom yang diperlukan (semua wajib):
- `nama_usaha` - Nama usaha
- `alamat` - Alamat lengkap
- `provinsi` - Nama provinsi (harus sesuai aplikasi)
- `kabupaten` - Nama kabupaten/kota
- `kecamatan` - Nama kecamatan
- `kelurahan` - Nama kelurahan/desa
- `latitude` - Koordinat latitude (desimal)
- `longitude` - Koordinat longitude (desimal)

## Cara Menggunakan

### 1. Melalui GUI (Recommended)

```bash
python run_matcha_gui.py
```

**Menu Update Usaha:**
1. Pilih file Excel
2. (Opsional) Atur range baris (start-end)
3. Klik `Mulai Proses`

**Menu Tambah Usaha Baru:**
1. Pilih file Excel khusus tambah usaha
2. (Opsional) Atur range baris
3. Klik `Mulai Proses`

**Menu Akun SSO:**
- Isi username dan password untuk auto-login (opsional)
- Tanpa ini, akan login manual setiap kali

### 2. Melalui CLI

```bash
# Update Usaha
python run_dirgc.py --start 1 --end 10

# Tambah Usaha Baru
python run_tambah_usaha.py
```

## Output Log

Setiap proses menghasilkan file Excel di `logs/YYYYMMDD/`:

**Kolom log:**
- `no` - Nomor baris Excel
- `idsbr` - ID usaha
- `nama_usaha` - Nama usaha
- `alamat` - Alamat
- `provinsi`, `kabupaten`, `kecamatan`, `kelurahan` (khusus tambah usaha)
- `keberadaanusaha_gc` - Kode hasil GC
- `latitude`, `longitude` - Koordinat
- `status` - Status proses (berhasil/gagal/skipped/error)
- `catatan` - Keterangan detail

## Troubleshooting

### Error: playwright not found
```bash
playwright install chromium
```

### Koordinat tidak ter-update
- Periksa apakah nilai di Excel sama dengan di aplikasi (akan di-skip)
- Periksa apakah field latitude/longitude visible di form
- Lihat log untuk detail: "Skip", "Update", atau "Fill"

### Nama wilayah tidak ditemukan (Tambah Usaha)
- Pastikan ejaan **persis** sesuai aplikasi MatchaPro
- Gunakan huruf kapital sesuai aplikasi
- Contoh: "Senapelan", bukan "senapelan" atau "SENAPELAN"

### Browser tidak muncul
- Jangan gunakan `--headless` untuk SSO login
- Pastikan tidak ada aplikasi yang memblokir browser

## Tips Penggunaan

1. **Test dengan data kecil dulu**: Gunakan `--start 1 --end 5` untuk test 5 baris
2. **Monitor log terminal**: Perhatikan pesan error atau warning
3. **Backup data Excel**: Simpan copy sebelum proses besar
4. **Nama wilayah**: Copy-paste dari aplikasi agar ejaan persis sama
5. **Koordinat**: Gunakan format desimal (contoh: 0.5304034)

## Kredit

Dikembangkan oleh Tim IPDS BPS Kabupaten Bulungan.

Semoga bermanfaat! 🚀
