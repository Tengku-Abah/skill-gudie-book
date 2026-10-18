# Application Guidebook Generator

Generator buku panduan operasional aplikasi (Application User Manual & SOP Deck) berbasis Python murni (`Pillow`). Mengubah spesifikasi terstruktur JSON atau YAML menjadi dokumen presentasi PDF beresolusi tinggi (format widescreen 16:9, 1920x1080), tangkapan layar slide individual PNG, dan web slide deck HTML interaktif yang dapat dibuka secara luring (offline).

Proyek ini dirancang agar tim pengembang, analis sistem, atau agen AI otonom dapat memproduksi buku manual teknis yang konsisten, terstandarisasi, dan rapi tanpa ketergantungan pada tool berat seperti browser crawling daemon atau office automation suite.

---

## 1. Persyaratan Sistem & Instalasi

### Persyaratan Minimum
- **Python**: Versi 3.10 atau lebih baru.
- **Sistem Operasi**: Windows, Linux, atau macOS.

### Langkah Instalasi Menggunakan Virtual Environment (venv)

```bash
# 1. Kloning atau arahkan ke direktori repositori
cd guidebook-generator

# 2. Buat virtual environment terisolasi
python -m venv venv

# 3. Aktifkan virtual environment
# Windows (cmd/bash):
# Git Bash saja:
source venv/Scripts/activate
# cmd.exe: venv\Scripts\activate.bat
# Windows (PowerShell):
# .\venv\Scripts\Activate.ps1
# Linux / macOS:
# source venv/bin/activate

# 4. Pasang pustaka dependensi minimum
pip install -r requirements.txt

# Opsional: Pasang dukungan YAML dan pengujian development
pip install -r requirements-dev.txt

# Atau pasang dalam mode editable menggunakan pyproject.toml:
pip install -e ".[dev]"
```

---

## 2. Perintah CLI (Command-Line Interface)

Engine `guidebook.py` menyediakan sub-perintah mandiri:

### a. Inisialisasi Template Spesifikasi Baru (`init`)
Membuat berkas rancangan spesifikasi awal berformat JSON atau YAML:
```bash
python guidebook.py init spec.json
# Atau format YAML jika PyYAML terpasang:
python guidebook.py init spec.yaml
```

### b. Validasi Sintaks & Ketersediaan Berkas (`validate`)
Memvalidasi struktur spec, format koordinat, serta memastikan seluruh berkas tangkapan layar tersedia dan tidak korup sebelum merender:
```bash
python guidebook.py validate spec.json
```

### c. Render Dokumen Panduan (`build`)
Membangun dokumen PDF, slide gambar PNG, dan slide deck interaktif HTML:
```bash
# Render PDF saja:
python guidebook.py build spec.json -o output/panduan.pdf

# Render lengkap (PDF + Ekspor PNG + Web Slide Deck HTML):
python guidebook.py build spec.json \
    -o output/panduan.pdf \
    --html \
    --export-images \
    --images-dir output/slides \
    --html-out output/index.html
```

---

## 3. Alur Kerja Agen & Panduan Standar Dokumentasi

Untuk menghasilkan buku manual operasional yang akurat dan berguna, agen dokumentasi maupun analis teknis mengikuti tahapan berikut:

### 1. Cakupan Fitur Sumber & Runtime (Feature Coverage)
- Telusuri pohon rute aplikasi, kontrol form UI, dan daftar aksi yang tersedia langsung dari kode sumber atau sesi runtime yang sah.
- Jangan hanya menyusun daftar menu; dokumentasikan **setiap fitur nyata** yang dapat dieksekusi pengguna.

### 2. Standar Deskripsi Per Fitur
Setiap fitur dalam slide panduan wajib menguraikan 6 aspek fundamental:
1. **Tujuan**: Apa urgensi dan manfaat bisnis fitur ini bagi pengguna.
2. **Kemampuan**: Apa saja aksi yang dapat dilakukan pada halaman/formulir tersebut (bisa melakukan apa saja).
3. **Langkah Operasional**: Urutan tombol, kolom input, dan navigasi yang harus ditekan (disinkronkan 1:1 dengan nomor callout badge).
4. **Hasil yang Diharapkan**: Respon visual atau status akhir sistem setelah aksi berhasil dieksekusi.
5. **Prasyarat & Hak Akses**: Role pengguna yang diizinkan (RBAC), data prasyarat, atau izin peramban (misal: GPS, kamera).
6. **Kendala & Solusi**: Solusi cepat bila terjadi kegagalan (misal: sesi kedaluwarsa, format data salah).

### 3. Matriks Bukti Otorisasi (Permissions Evidence Matrix)
Buku panduan harus secara tegas membedakan hak akses antar-peran (Role-Based Separation), contoh:

Contoh hipotetis, bukan hak akses aplikasi yang sudah diverifikasi. Ganti seluruh baris berdasarkan bukti; Admin tidak otomatis memiliki akses lintas tenant.

| Peran (Role) | Hak Akses Modul | Aksi yang Diizinkan | Batasan (Limitations) |
|---|---|---|---|
| **Operator / Peserta** | Form Pengisian, Dashboard Pribadi | Mengisi draft, memvalidasi profil, submit akhir | Tidak dapat mengekspor rekapitulasi data global |
| **Admin Cabang** | Monitoring Lokal, Verifikasi Peserta | Reset status peserta, periksa log kehadiran | Terbatas pada wilayah kerja cabang terkait |
| **Admin Pusat / TA** | Manajemen Global, Konfigurasi Sistem | Ekspor rekapitulasi Excel/PDF, audit log, buka kunci | Akses penuh seluruh tenant |

### 4. Kebijakan Keamanan & Privasi Data (Read-Only & Redaksi)
- **Akses Read-Only**: Agen hanya mengamati antarmuka; tidak menyimpan password akun, token API aktif, atau kredensial produksi ke dalam berkas spec.
- **Redaksi Gambar Akhir**: Tangkapan layar formulir wajib menyamarkan data sensitif pengguna (NIK, nomor HP pribadi, alamat email riil, nomor rekening) menggunakan array `redact`:
  ```json
  "redact": [
    [10.0, 50.0, 30.0, 8.0]
  ]
  ```
  Sistem secara otomatis menimpa koordinat tersebut dengan blok solid berlabel `[DIREDAKSI]` pada berkas citra akhir sebelum masuk ke PDF.

---

## 4. Tipe Slide yang Didukung

Kanvas berukuran standar 16:9 (`1920x1080 px`). Tipe slide deklaratif yang tersedia:

| Tipe Slide (`type`) | Fungsi & Elemen Utama |
|---|---|
| `cover` | Sampul utama: Judul modul, subjudul, nama penyusun, organisasi, dan pill status metadata. |
| `cards` | Kartu metrik / struktur modul: Angka highlight besar (hero metrics), unit, dan deskripsi ringkas. |
| `checklist` | Ketentuan pelaksanaan: Kartu tata tertib dua kolom dengan lencana urutan bernomor. |
| `roadmap` | Horizontal pipeline: Urutan tahapan besar alur sistem (Step 01 - Step 05) lengkap dengan panah alur. |
| `timeline` | Rundown / jadwal: Baris jadwal kegiatan dan badge durasi menit warna kontras tinggi. |
| `section_header` | Slide pembatas bab / peran: Transisi peran pengguna (misal: modul peserta ke admin). |
| `step` | Panduan prosedural: Screenshot UI di panel kiri (65%), kotak anotasi, badge 1:1, dan panel instruksi kanan. |
| `feature` | Eksplorasi fitur: Screenshot UI di kiri + daftar kemampuan ("BISA MELAKUKAN APA SAJA?") di panel kanan. |
| `faq` | Matriks kendala: Pertanyaan cetak tebal dan solusi perbaikan instan. |
| `outro` | Penutup: Ucapan penutup, himbauan logout, dan kotak kontak bantuan / helpdesk. |

---

## 5. Konfigurasi Font Portabel (Cross-Platform Fallback)

Mesin `FontManager` mendeteksi font TrueType sistem secara otomatis:
- **Windows**: `Segoe UI` (`segoeui.ttf`, `segoeuib.ttf`), `Arial`, `Calibri`.
- **Linux**: `DejaVu Sans`, `Liberation Sans`, `FreeSans`.
- **macOS**: `Helvetica.ttc`, `SFNSText.ttf`.

### Pengaturan Font Manual (Override)
Jika dijalankan di container Docker atau distro Linux minimal yang belum memiliki paket font standar, gunakan environment variable untuk menentukan path font:

```bash
export GUIDEBOOK_FONT_REG="/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
export GUIDEBOOK_FONT_BOLD="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
python guidebook.py build spec.json -o panduan.pdf
```

---

## 6. Contoh Sintetis (Synthetic Demo)

Repositori menyediakan contoh sintetis lengkap yang bebas dari data privat pada direktori `examples/`:

```bash
# 1. Hasilkan aset dummy sintetis dan file demo.json:
python examples/make_demo.py

# 2. Uji validasi spec contoh:
python guidebook.py validate examples/demo.json

# 3. Bangun dokumen demo:
python guidebook.py build examples/demo.json -o output/demo.pdf --html --export-images --images-dir output/slides --html-out output/index.html
```

---

## 7. Skill Agent Portabel (`skills/application-guidebook/`)

Repositori ini menyertakan definisi standar skill siap pakai pada `skills/application-guidebook/SKILL.md`.
- **Pemasangan Mandiri (Manual)**: Untuk memasang pada agent Hermes atau runtime agent AI lainnya, salin direktori `skills/application-guidebook/` ke folder skill lokal Anda (misal: `~/.hermes/skills/productivity/application-guidebook/`).
- **Bukan Integrasi Otomatis**: Repositori ini tidak mengklaim integrasi global otomatis ke agent mana pun; pengembang mengonfigurasi direktori tujuan sesuai lingkungan masing-masing.

---

## 8. Pengujian, koordinat, dan batasan

```bash
python -m unittest discover -s tests -v
python tests/check_artifacts.py output/demo.pdf output/index.html
```

Dukungan YAML saja: `python -m pip install ".[yaml]"`. Command terpasang: `guidebook --help`.
Semua output relatif current working directory; screenshot relatif lokasi spec. `--html` otomatis
mengekspor PNG; bagikan HTML bersama direktori slide, bukan HTML sendirian.
`-o folder` tanpa ekstensi menghasilkan `folder/guidebook.pdf`. HTML/gambar harus satu drive.
`init` menghasilkan satu cover DEMO; tambahkan fitur dan screenshot nyata sebelum dipakai.

Lihat [workflow/evidence dan koordinat](docs/WORKFLOW.md),
[referensi spec](skills/application-guidebook/references/spec-schema.md),
[catatan review/batasan](docs/REVIEW.md). Redaksi tidak mengubah screenshot sumber.
Periksa gambar final, bukan sekadar kotak koordinat. Jangan sertakan raw capture privat dalam publikasi.
Skill merupakan prosedur portabel; dukungan discovery/loading mengikuti agent tujuan, tidak otomatis.

## 9. Lisensi

Status lisensi: **Licensing pending owner decision**.
Lihat berkas `LICENSE` untuk rincian status hak cipta dan lisensi resmi.
