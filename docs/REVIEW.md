# Catatan review lokal

Paket staging, belum rilis. Lisensi dan pemilik belum ditentukan. Tidak ada remote/push/commit.
Engine asli dibaca seluruhnya (1151 baris); renderer Pillow dipertahankan.

Perubahan: validasi struktur/aset/koordinat; HTML escape judul/organisasi dan encoding path;
HTML menghitung path gambar relatif ke lokasi HTML; pixel callout mengikuti skala gambar;
font override dan fallback scalable; init kini template cover generik buildable tanpa aset privat.
Flag CLI lama tetap tersedia; `validate` ditambahkan. `-o folder` tetap menghasilkan `folder/guidebook.pdf`.

Keterbatasan: layout tetap, tidak ada auto-pagination/overflow detector, HTML/PDF berupa gambar
(tidak menyediakan teks aksesibel/searchable lengkap). Pisah slide panjang; siapkan teks manual
pendamping bila dibutuhkan. Tidak ada crawler, capture engine atau pengujian RBAC otomatis.
Input spec hanya dari sumber tepercaya: path lokal dapat mengakses gambar di luar repo.

CI disiapkan untuk Linux/Windows Python 3.10/3.12; hasil remote belum dijalankan sampai publikasi.
Dependency rentang minimum, bukan lockfile reproducible. Review lisensi dependensi/aset sebelum rilis.
