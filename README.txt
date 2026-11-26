APLIKASI PEMESANAN TIKET EVENT (Python Tkinter)

FITUR
- Login awal
- Dashboard statistik event, transaksi, tiket terjual, pendapatan
- CRUD dasar data event (tambah dan hapus)
- Kategori tiket, harga, dan kuota
- Pemesanan tiket dengan validasi kuota dan kode tiket otomatis
- Perhitungan total biaya dan pencatatan pembayaran
- Laporan penjualan
- Ekspor laporan Excel (.xlsx) dan PDF
- Backup database SQLite

LOGIN DEMO
Username: admin
Password: admin123
Ganti password demo sebelum digunakan sungguhan (hash password saat ini SHA-256 sederhana).

CARA MENJALANKAN (Windows)
1. Install Python 3.10 atau lebih baru. Pastikan opsi "Add Python to PATH" dicentang.
2. Ekstrak ZIP ini.
3. Buka folder dengan VS Code.
4. Buka Terminal, jalankan:
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   python app.py

Secara default aplikasi memakai SQLite lokal dan langsung membuat database event_ticket.db.
Untuk memakai MySQL XAMPP:
1. Jalankan Apache dan MySQL dari XAMPP.
2. Buka phpMyAdmin, import schema_mysql.sql.
3. Salin .env.example menjadi .env dan sesuaikan pengaturan koneksi.
4. Atur USE_MYSQL=1. Install python-dotenv jika ingin membaca .env otomatis; atau set variabel DB_* di terminal Windows sebelum menjalankan app.
   Catatan: aplikasi tidak membaca file .env otomatis. Cara cepat: salin nilai variabel dari .env ke Environment Variables Windows / terminal.
5. Jalankan python app.py. Login awal: admin / admin123.

CATATAN
- SQLite digunakan sebagai mode awal agar aplikasi dapat langsung diuji tanpa konfigurasi server.
- Untuk mode MySQL, tabel harus dibuat terlebih dahulu dengan schema_mysql.sql.
- Pembayaran pada versi awal dicatat sebagai Tunai/Lunas (simulasi, bukan payment gateway).
- Data contoh event dan kategori otomatis dibuat pada mode SQLite pertama kali.
