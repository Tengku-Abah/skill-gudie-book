"""Generate synthetic screenshots and demo spec without real application data."""
from pathlib import Path
import json
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
ASSETS = ROOT / "assets"
ASSETS.mkdir(parents=True, exist_ok=True)

def create_synthetic_image(filename: str, title: str, subtitle: str, color: str, extra: str = ""):
    img = Image.new("RGB", (1280, 720), "#0f172a")
    d = ImageDraw.Draw(img)
    d.rectangle([20, 20, 1260, 700], fill="#1e293b", outline="#334155", width=2)
    d.rectangle([20, 20, 1260, 80], fill=color)
    d.text((40, 35), "[SYNTHETIC DEMO SCREEN - TEST PURPOSES ONLY]", fill="#ffffff")
    d.rectangle([60, 120, 1220, 200], fill="#334155")
    d.text((80, 140), title, fill="#ffffff")
    d.text((80, 168), subtitle, fill="#94a3b8")
    d.rectangle([60, 230, 600, 500], fill="#0f172a", outline="#475569", width=2)
    d.text((80, 250), "Input Panel / Form Control", fill="#e2e8f0")
    d.rectangle([80, 300, 580, 350], fill="#1e293b", outline="#64748b", width=1)
    d.text((95, 318), "field: demo_user_account", fill="#94a3b8")
    d.rectangle([80, 380, 580, 430], fill="#1e293b", outline="#64748b", width=1)
    d.text((95, 398), "field: secret_token_masked (1234567890123456)", fill="#94a3b8")
    d.rectangle([640, 230, 1220, 500], fill="#0f172a", outline="#475569", width=2)
    d.text((660, 250), "Preview Panel / Data Table", fill="#e2e8f0")
    for idx, row in enumerate(["Record A - Status: Ready", "Record B - Status: Pending", "Record C - Status: Completed"]):
        ry = 300 + (idx * 50)
        d.rectangle([660, ry, 1200, ry + 40], fill="#1e293b")
        d.text((680, ry + 12), row, fill="#cbd5e1")
    if extra:
        d.text((60, 540), extra, fill="#38bdf8")
    d.rectangle([20, 660, 1260, 700], fill="#0f172a")
    d.text((40, 672), "CONFIDENTIALITY: No live user data, passwords, or production secrets are displayed.", fill="#64748b")
    out = ASSETS / filename
    img.save(out)
    return str(out)

img1 = create_synthetic_image("demo_login.png", "Aplikasi Demo: Form Otentikasi & Masuk", "Akses akun menggunakan identitas berwenang", "#2563eb", "Role: Operator / Pengguna")
img2 = create_synthetic_image("demo_dashboard.png", "Aplikasi Demo: Ringkasan Fitur & Menu", "Panel navigasi utama sistem pencatatan", "#059669", "Role: Administrator")

spec = {
    "title": "PANDUAN APLIKASI CONTOH (SYNTHETIC DEMO)",
    "subtitle": "Panduan Standar Operasional Pengguna Sistem Web",
    "organization": "DEMO ENTERPRISE LABS",
    "author": "Tim Teknis & Pengembang Panduan",
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
    "slides": [
        {
            "type": "cover",
            "title": "PANDUAN SISTEM ENTERPRISE",
            "subtitle": "Petunjuk Operasional Berbasis Tangkapan Layar",
            "description": "Dokumen ini menyajikan alur operasional standar sistem. Seluruh tangkapan layar dalam panduan ini merupakan data sintetis (dummy) dan bebas dari data pribadi maupun kredensial produksi.",
            "meta": ["Versi 1.0 (Demo)", "Resolusi 16:9", "Akses Read-Only"]
        },
        {
            "type": "cards",
            "title": "Struktur Modul & Cakupan Sistem",
            "category": "RINGKASAN",
            "items": [
                {"title": "Modul Inti", "value": "04", "unit": "Modul Aktif", "description": "Otentikasi, Dashboard, Pencatatan, dan Laporan.", "highlight": True},
                {"title": "Hak Akses", "value": "02", "unit": "Role RBAC", "description": "Pemisahan peran Operator dan Administrator Pusat."},
                {"title": "Target Waktu", "value": "15", "unit": "Menit SLA", "description": "Waktu penyelesaian alur normal tanpa eskalasi."}
            ]
        },
        {
            "type": "roadmap",
            "title": "Peta Alur Kerja Pengguna",
            "steps": [
                {"label": "LANGKAH 01", "title": "Buka Aplikasi", "description": "Buka URL resmi melalui peramban yang didukung."},
                {"label": "LANGKAH 02", "title": "Otentikasi Akun", "description": "Masukkan username dan kata sandi yang sah."},
                {"label": "LANGKAH 03", "title": "Verifikasi Profil", "description": "Pastikan nama dan hak akses sesuai tugas."},
                {"label": "LANGKAH 04", "title": "Pencatatan", "description": "Isi data formulir dan simpan sebagai draft."},
                {"label": "LANGKAH 05", "title": "Selesai", "description": "Periksa rekapitulasi data dan keluar sistem."}
            ]
        },
        {
            "type": "step",
            "role": "PANDUAN OPERATOR",
            "step_number": 1,
            "title": "Otentikasi dan Masuk ke Dashboard",
            "screenshot": "assets/demo_login.png",
            "purpose": "Panduan mengisi formulir otentikasi akun operator untuk mengakses menu operasional.",
            "actions": [
                "Ketikkan ID akun atau email operasional pada kolom akun.",
                "Ketikkan kata sandi resmi lalu tekan tombol Masuk Sistem."
            ],
            "warning": "Dilarang membagikan kredensial atau menyimpan kata sandi di komputer publik!",
            "notes": "Jika lupa kata sandi, hubungi admin untuk reset token.",
            "coordinate_units": "percent",
            "redact": [
                [6.2, 52.5, 40.0, 7.5]
            ],
            "callouts": [
                {"box": [6.2, 41.5, 40.0, 7.5], "color": "accent", "auto_badge": True},
                {"box": [6.2, 52.5, 40.0, 7.5], "color": "primary", "auto_badge": True}
            ]
        },
        {
            "type": "feature",
            "role": "PANDUAN ADMINISTRATOR",
            "step_number": 2,
            "title": "Eksplorasi Fitur Dashboard & Monitor Rekap",
            "screenshot": "assets/demo_dashboard.png",
            "purpose": "Halaman utama untuk memantau status antrean data, log aktivitas, dan ekspor dokumen.",
            "capabilities": [
                {"name": "Filter Status Rekap", "desc": "Menyaring daftar entri berdasarkan status (Ready, Pending, Completed)."},
                {"name": "Ekspor Laporan", "desc": "Mengunduh berkas laporan dalam format PDF atau spreadsheet tabular."},
                {"name": "Audit Log", "desc": "Memeriksa riwayat modifikasi data beserta timestamp dan aktor pengubah."}
            ],
            "limitations": "Hanya role Administrator yang memiliki akses ke menu ekspor data global.",
            "coordinate_units": "percent",
            "callouts": [
                {"box": [50.0, 41.5, 45.0, 28.0], "color": "accent", "auto_badge": True}
            ]
        },
        {
            "type": "faq",
            "title": "Kendala Lapangan & Solusi Cepat",
            "items": [
                {"question": "Bagaimana jika form menolak input dengan pesan 'Session Expired'?", "answer": "Muat ulang halaman browser dan lakukan login ulang menggunakan akun yang sama."},
                {"question": "Mengapa tombol ekspor laporan tidak aktif pada akun operator?", "answer": "Fitur ekspor dibatasi hanya untuk role Administrator sesuai matriks otorisasi RBAC."}
            ]
        },
        {
            "type": "outro",
            "title": "SELESAI & PENUTUP",
            "message": "Seluruh alur operasional sistem selesai diuraikan. Pastikan selalu keluar dari akun setelah selesai beraktivitas di perangkat bersama.",
            "contact": "Kanal Bantuan Teknis: demo-helpdesk@example.com"
        }
    ]
}

(ROOT / "demo.json").write_text(json.dumps(spec, indent=2, ensure_ascii=False), encoding="utf-8")
print("Synthetic demo assets and spec generated successfully!")
