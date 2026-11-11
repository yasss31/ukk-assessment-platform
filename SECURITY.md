# Protokol Keamanan & Perlindungan Kredensial

Platform ini mengimplementasikan langkah-langkah keamanan ketat untuk menjamin integritas sesi AWS Academy dan kepatuhan privasi data sekolah.

---

## 1. Zero Credential Persistence Policy (In-Memory Processing)
- Kredensial AWS Academy (`aws_access_key_id`, `aws_secret_access_key`, `aws_session_token`) yang dimasukkan oleh penguji **hanya diproses di dalam memori kerja (RAM)** server selama audit API berlangsung.
- Kredensial AWS **TIDAK PERNAH** ditulis ke dalam file JSON, database lokal, log aplikasi, Google Spreadsheet, atau penyimpanan persisten apa pun.
- Setelah proses audit indikator selesai, referensi sesi AWS langsung dihapus dari memori.

---

## 2. Perlindungan Kata Sandi & Sesi Penguji
- Kata sandi penguji disimpan menggunakan algoritma **HMAC-SHA256 ber-salt** yang unik per instalasi.
- Token autentikasi menggunakan **JSON Web Token (JWT)** yang ditandatangani secara kriptografis dengan masa kedaluwarsa otomatis (1440 menit / 24 jam).

---

## 3. Pencegahan Kebocoran Rahasia di Git
- File `.gitignore` secara tegas mengecualikan:
  - File rahasia `.env`
  - Kunci privat SSH (`*.pem`, `*.key`)
  - File kredensial Google Service Account (`service_account.json`)
  - Folder data penilaian lokal (`local_storage/`)
  - Virtual environment (`venv/`) dan dependensi (`node_modules/`)

---

## 4. Keamanan Audit AWS (Read-Only)
- Modul penilaian (`assessment_engine.py`) secara eksklusif hanya memanggil operasi **Read-Only / Describe / Get** pada API AWS SDK (seperti `describe_vpcs`, `describe_subnets`, `describe_instances`, `get_caller_identity`).
- Sistem tidak pernah mengubah, menghapus, atau membuat resource di akun AWS peserta selama sesi penilaian.
- Pada fitur AWS Auto Play, pemanggilan `start_instances` dibatasi secara ketat hanya untuk instance EC2 berstatus `stopped` dengan protokol idempotensi.
