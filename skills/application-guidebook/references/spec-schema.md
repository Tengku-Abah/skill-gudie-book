# Guidebook Specification Reference

Format file: JSON atau YAML. Dimensi kanvas output: 1920x1080 px (16:9 widescreen).

## Struktur Root

```json
{
  "title": "Nama Panduan Aplikasi",
  "subtitle": "Subjudul Tambahan",
  "organization": "Nama Organisasi",
  "author": "Penyusun Dokumen",
  "theme": {
    "primary": "#2563eb",
    "primary_dark": "#1d4ed8",
    "secondary": "#0f172a",
    "accent": "#059669",
    "warning": "#d97706",
    "danger": "#dc2626",
    "bg": "#f8fafc",
    "card_bg": "#ffffff",
    "text_main": "#0f172a",
    "text_muted": "#475569",
    "border": "#e2e8f0"
  },
  "slides": []
}
```

## Jenis Slide (`type`)

1. `cover`: Halaman judul dengan chip metadata dan kartu pengantar.
2. `cards`: Ringkasan modul/metrik (kolom kartu highlight).
3. `checklist`: Tata tertib, prasyarat perangkat, dan aturan operasional.
4. `roadmap`: Diagram alur proses horizontal bertahap (Step 01 ke Step 05).
5. `timeline`: Jadwal alur kegiatan dan durasi pelaksanaan.
6. `section_header`: Pembatas bab/peran (PANDUAN OPERATOR, ADMIN).
7. `step`: Prosedur langkah demi langkah dengan screenshot beranotasi di kiri dan daftar tindakan di kanan.
8. `feature`: Eksplorasi kemampuan fitur ("BISA MELAKUKAN APA SAJA?") dengan screenshot.
9. `faq`: Pertanyaan umum dan panduan solusi kendala instan.
10. `outro`: Halaman penutup dengan kontak layanan bantuan / helpdesk.

## Anotasi Tangkapan Layar (`step` & `feature`)

```json
{
  "type": "step",
  "role": "PANDUAN OPERATOR",
  "step_number": 1,
  "title": "Otentikasi Akun",
  "screenshot": "assets/login.png",
  "purpose": "Akses halaman login resmi dan masukkan kredensial yang sah.",
  "actions": [
    "Masukkan nama pengguna atau email resmi.",
    "Masukkan kata sandi lalu klik tombol Masuk Sistem."
  ],
  "coordinate_units": "percent",
  "redact": [
    [10.0, 50.0, 30.0, 8.0]
  ],
  "callouts": [
    {"box": [10.0, 40.0, 30.0, 8.0], "color": "accent", "auto_badge": true},
    {"box": [10.0, 50.0, 30.0, 8.0], "color": "primary", "auto_badge": true}
  ]
}
```
