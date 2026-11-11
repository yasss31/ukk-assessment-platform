# UKK Assessment Platform — Cloud Engineer 2026/2027
### Sistem Otomatisasi Penilaian Infrastruktur Cloud & Manajemen Rubrik Dinamis
**SMK Negeri 1 Banyumas — Program Makan Bergizi Gratis (MBG) Revisi 1**

---

## 🌟 Ringkasan Platform

**UKK Assessment Platform** adalah aplikasi web modern yang dirancang khusus untuk mempermudah dan mempercepat proses pengujian Uji Kompetensi Keahlian (UKK) Cloud Engineer. Penguji cukup memilih siswa, menentukan profil rubrik penilaian yang diinginkan, dan memasukkan kredensial AWS Academy sementara milik peserta.

Sistem secara otomatis akan melakukan audit *read-only* terhadap seluruh infrastruktur cloud AWS peserta, memvalidasi 17 aspek penilaian, menghitung nilai terbobot secara transparan, serta menyinkronkan hasil ke **Google Spreadsheet** dan mencetak lembar nilai resmi.

---

## 🚀 Jawaban: GitHub vs VPS Pribadi + Cloudflare Tunnel

Pengguna menanyakan:
> *"apakah cukup hanya menggunakan github yg simple tinggal akses web dan masukan credential lalu jalanin atau pake vps aku punya vps soalnya"*

### Analisis & Rekomendasi:

| Kriteria | Opsi A: Hanya GitHub Pages / Vercel (Frontend Saja) | Opsi B: VPS Pribadi + Cloudflare Tunnel (Direkomendasikan ⭐) |
| :--- | :--- | :--- |
| **Kemampuan Eksekusi** | ❌ **Tidak Bisa Mandiri.** AWS SDK (Boto3) & validasi port/session butuh runtime backend (Python/Node). GitHub Pages hanya menyajikan static file HTML/JS. Jika browser langsung memanggil AWS API, akan terbentur kendala CORS dan token security. | ✅ **100% Berfungsi Penuh.** VPS menjalankan backend FastAPI (Boto3 + Google Sheets API) dan frontend Nginx/Vite secara aman dan terisolasi. |
| **Keamanan Kredensial AWS** | ❌ Berisiko jika dieksekusi di browser publik client-side. | ✅ **Sangat Aman.** Kredensial AWS hanya berada di memori RAM backend VPS selama proses audit berlangsung (*in-memory*), lalu langsung dibuang. |
| **Domain & Akses Penguji** | Butuh hosting backend terpisah. | ✅ **Sangat Mudah & Profesional.** Menggunakan `cloudflared` (Cloudflare Tunnel), VPS Anda langsung terhubung ke domain kustom Anda (misal: `ukk.domainanda.com`) tanpa perlu IP Publik Statis, tanpa bayar SSL, dan tanpa perlu membuka port router. |
| **Penyimpanan Nilai** | Terbatas. | ✅ Nilai tersimpan di database lokal VPS sekaligus otomatis tersinkronisasi ke Google Spreadsheet panitia. |

**Kesimpulan:** Gunakan **VPS milik Anda** sebagai server aplikasi penilaian, lalu gunakan **Cloudflare Tunnel (`cloudflared`)** untuk mengarahkan domain kustom ke VPS tersebut. Kode proyek disimpan di GitHub untuk version control dan backup.

Panduan langkah demi langkah pemasangan domain Cloudflare di VPS tersedia di [CLOUDFLARE_VPS_GUIDE.md](./CLOUDFLARE_VPS_GUIDE.md).

---

## 🔑 Fitur Utama

### 1. Dynamic Rubric Engine (Rubrik Tidak Statis)
- Dilengkapi profil bawaan resmi: **UKK Cloud Engineer 2026/2027 - MBG (Revisi 1)** dengan total bobot tepat 100.0.
- **Kustomisasi Bobot:** Penguji dapat menyesuaikan bobot masing-masing indikator.
- **Duplikasi Profil:** Penguji dapat membuat salinan rubrik dengan kriteria berbeda untuk tiap sesi ujian (misal: Sesi Remedial, Sesi Khusus, atau Paket Soal Alternatif).

### 2. Audit Otomatis 17 Aspek Arsitektur AWS (Read-Only)
Sistem melakukan verifikasi tanpa mengubah arsitektur peserta:
1. **mbg-vpc** (CIDR 10.20.0.0/16, DNS Hostnames & Resolution).
2. **7 Subnets** (2 Public ALB, 2 Private FE, 1 Private BE, 2 Isolated DB).
3. **mbg-igw** (Internet Gateway terpasang ke VPC).
4. **mbg-natgw-1a** (NAT Gateway di subnet public 1a dengan Elastic IP).
5. **Route Tables** (Public -> IGW, Private -> NAT GW, DB -> Lokal).
6. **5 Security Groups** (ALB, FE, BE, RDS, EFS dengan aturan port 2049 eksklusif).
7. **RDS MySQL** (`mbg-rds-mysql`, db.t3.micro, multi-AZ DB Subnet Group, private).
8. **S3 Bucket Regional** (`mbg-uploads-*`, 100% Block Public Access, folder `aduan/` & `laporan/`).
9. **SNS Notifikasi** (`mbg-sns-notifikasi`, Subscription email BGN terkonfirmasi).
10. **EC2 Back End** (`mbg-ec2-be`, private subnet, tanpa IP publik).
11. **Launch Template** (`mbg-lt-fe`, custom AMI `mbg-ami-fe` Revisi 1, script auto-mount EFS).
12. **Auto Scaling Group** (`mbg-asg-fe`, kapasitas 2/2/4, multi-AZ, minimal 2 InService).
13. **Target Group** (`mbg-tg-fe`, health path `/health.php`, 2 targets Healthy).
14. **Dynamic Scaling Policy** (Target Tracking CPUUtilization 50% pada ASG).
15. **Application Load Balancer** (`mbg-alb-fe`, internet-facing, DNS HTTP 200).
16. **Shared Session EFS** (`mbg-efs-fe-session`, multi-AZ Mount Target, `/mnt/efs/mbg-session`).
17. **End-to-End Workflow Testing** (Login 3 role: bgn, sppg1, masy1, submit aduan, upload bukti ke S3).

### 3. AWS Auto Play Manager (Aman & Hemat Biaya)
- Saklar **ON/OFF** terjadwal (interval standar 180 menit / 3 jam).
- **Protokol Idempotensi:** Hanya menyalakan EC2 yang berstatus `stopped`. Jika instance sudah `running`, sistem tidak mengirim panggilan API (NOOP).
- **Eksekusi Manual Seketika:** Tombol untuk menyalakan instance lab peserta saat pengujian akan dimulai.
- **Audit Logs:** Riwayat aksi tercatat lengkap dengan timestamp dan status.

### 4. Sinkronisasi Google Sheets & Cadangan Lokal
- Terhubung langsung ke Google Spreadsheet ID: `1Ri7F8T7YTQdr7F71aslfVpIfYrSva_F0dmtbT5tBJW8`.
- **Desain Tahan Gangguan:** Jika Service Account Google belum dikonfigurasi, sistem otomatis beralih ke mode penyimpanan lokal (`local_storage/`) tanpa crash.
- **Ekspor Nilai:** Unduh rekapitulasi penilaian dalam format **JSON**, **CSV**, atau **Lembar Nilai Siap Cetak (HTML/PDF)**.

### 5. Keamanan Tingkat Tinggi
- Kredensial AWS Academy hanya disimpan sementara di RAM (*in-memory*) selama evaluasi dan **tidak pernah ditulis ke disk atau database**.
- Kata sandi admin di-hash dengan HMAC-SHA256 ber-salt.

---

## 🛠️ Panduan Menjalankan di Komputer Lokal / Pengujian

### Prasyarat
- Python 3.10+
- Node.js 18+ & npm

### 1. Menjalankan Backend (FastAPI)
```powershell
cd D:\LKPD\ukk-assessment-platform\backend

# Mengaktifkan virtual environment
.\venv\Scripts\Activate.ps1

# Menjalankan server backend
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```
Akses API Docs Swagger di: `http://localhost:8000/docs`

### 2. Menjalankan Frontend (React + Vite + Tailwind)
```powershell
cd D:\LKPD\ukk-assessment-platform\frontend

# Menjalankan dev server frontend
npm run dev
```
Buka peramban di: `http://localhost:5173`

**Akun Login Default:**
- Username: `admin`
- Password: `adminukk2026`

---

## 🐳 Menjalankan dengan Docker Compose (VPS)

```bash
# Clone repository di VPS
git clone https://github.com/yasss31/ukk-assessment-platform.git
cd ukk-assessment-platform

# Jalankan backend dan frontend
docker compose up -d --build
```
Aplikasi langsung berjalan di port 80 VPS.

---

## 📄 Lisensi
Hak Cipta © 2026 SMK Negeri 1 Banyumas. Dikembangkan untuk Uji Kompetensi Keahlian (UKK) Teknik Komputer dan Jaringan / Cloud Computing.
