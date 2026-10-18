# Bukti dan koordinat

## Matriks cakupan (isi setiap fitur dan role)
| ID fitur | Role | Route/menu/subfitur | Sumber file:baris/revisi | Runtime screenshot/tanggal | Aksi diuji? | Hasil | Halaman | Status |
|---|---|---|---|---|---|---|---|---|
| DEMO-01 | Operator DEMO | Form DEMO | examples/make_demo.py | sintetis, bukan runtime nyata | tidak | ilustrasi | 4 | DEMO |

Status: source-only, runtime-observed, action-tested, blocked, not-verified.
Menu tersembunyi bukan bukti otorisasi server. Catat expected/observed allow/deny per role,
lingkup tenant, prasyarat dan alasan belum diuji. Jangan menaikkan status hanya karena render lulus.

Default akses read-only. Jangan submit/delete/reset/export data privat atau ubah akun produksi.
Login memakai tool aman agent atau dilakukan sendiri oleh user; jangan kumpulkan password/token.
Screenshot diambil memakai browser/desktop tool agent yang sudah ada, dengan scope disetujui user.

Per fitur catat tujuan, seluruh kemampuan, urutan tombol/kolom, hasil, prasyarat/role,
kendala dan solusi berbukti. Gunakan feature untuk kemampuan, step untuk prosedur,
notes untuk hasil/prasyarat, limitations untuk batasan, faq untuk kendala; pecah ke slide tambahan
bila panjang. Tidak ada field hasil/prasyarat khusus yang otomatis dirender.

## Koordinat
`coordinate_units`: percent disarankan, pixels eksplisit, auto kompatibilitas lama.
Rectangle `[x,y,w,h]`: ukuran positif, seluruh area harus berada dalam gambar.
Crop relatif gambar asli; redact dan callout relatif gambar SETELAH crop.
Resize display otomatis; hitung ulang anotasi setelah crop berubah. Arrow selalu persen.
Legacy auto: rectangle dianggap persen bila x dan y <=100, selainnya pixel; hindari ambiguitas.

## Gate publikasi
Render satu halaman dulu. Periksa semua final PNG dan halaman PDF: teks tidak meluap,
nomor cocok secara semantik, redaksi benar-benar menutup data. Sumber screenshot tidak diubah
oleh redaksi: simpan raw captures/spec privat di luar folder publikasi, jangan hanya mengandalkan gitignore.
Buka ulang PDF, cek jumlah/rasio halaman, buka HTML offline, coba Next/Prev/keyboard.
PDF/PNG raster, bukan dokumen teks aksesibel; sediakan panduan teks bila dibutuhkan.
