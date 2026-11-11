# Panduan Menghubungkan Domain ke VPS Menggunakan Cloudflare Tunnel (`cloudflared`)

Panduan ini menjelaskan cara mempublikasikan **UKK Assessment Platform** yang berjalan di VPS Anda agar dapat diakses oleh para penguji melalui domain pribadi (misalnya `ukk.domainanda.com`) tanpa perlu membuka port router/firewall dan sudah otomatis mendapatkan sertifikat SSL HTTPS gratis dari Cloudflare.

---

## 🎯 Keuntungan Menggunakan Cloudflare Tunnel

1. **Tanpa Port Forwarding:** Anda tidak perlu membuka port 80/443 di firewall VPS Anda.
2. **IP VPS Tersembunyi:** IP publik VPS Anda aman dari serangan DDoS dan pemindaian port publik.
3. **SSL/HTTPS Otomatis:** Koneksi terenkripsi penuh tanpa perlu repot mengonfigurasi Let's Encrypt / Certbot.
4. **Gratis:** Fitur Cloudflare Zero Trust / Tunnel tersedia secara gratis.

---

## 📋 Langkah-langkah Konfigurasi di VPS

### Langkah 1: Siapkan Aplikasi di VPS dengan Docker Compose
Masuk ke terminal SSH VPS Anda:
```bash
# 1. Update paket sistem
sudo apt update && sudo apt install -y curl git docker.io docker-compose-v2

# 2. Clone repository UKK Assessment Platform
git clone https://github.com/yasss31/ukk-assessment-platform.git
cd ukk-assessment-platform

# 3. Jalankan container
docker compose up -d --build

# 4. Verifikasi bahwa frontend dan backend aktif
docker compose ps
curl http://localhost:80
```

---

### Langkah 2: Pasang `cloudflared` di VPS
Jalankan perintah berikut di VPS (Linux x86_64 / amd64):
```bash
# Unduh binary resmi cloudflared
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb

# Pasang paket
sudo dpkg -i cloudflared.deb
```

---

### Langkah 3: Hubungkan `cloudflared` dengan Akun Cloudflare

Jalankan perintah login:
```bash
cloudflared tunnel login
```
Terminal akan menampilkan sebuah tautan URL. Buka tautan tersebut di peramban web komputer Anda, lalu pilih domain yang ingin Anda gunakan. Setelah diotorisasi, file sertifikat `cert.pem` akan otomatis tersimpan di `~/.cloudflared/cert.pem` di VPS.

---

### Langkah 4: Buat Tunnel Baru
Beri nama tunnel Anda, misalnya `ukk-tunnel`:
```bash
cloudflared tunnel create ukk-tunnel
```
Catat **Tunnel ID** (string UUID panjang) yang muncul di layar terminal.

---

### Langkah 5: Buat File Konfigurasi Tunnel
Buat file `config.yml` di folder `~/.cloudflared/`:
```bash
nano ~/.cloudflared/config.yml
```
Isi dengan konfigurasi berikut (ganti `<TUNNEL_ID>` dan `<domainanda.com>`):
```yaml
tunnel: <TUNNEL_ID>
credentials-file: /root/.cloudflared/<TUNNEL_ID>.json

ingress:
  # Arahkan domain ke frontend aplikasi (port 80)
  - hostname: ukk.domainanda.com
    service: http://localhost:80
  # Catch-all default 404
  - service: http_status:404
```
Simpan file (`Ctrl + O`, lalu `Enter`, lalu `Ctrl + X`).

---

### Langkah 6: Hubungkan Subdomain DNS di Cloudflare
Arahkan subdomain Anda ke tunnel:
```bash
cloudflared tunnel route dns ukk-tunnel ukk.domainanda.com
```
Perintah ini akan secara otomatis menambahkan CNAME record di dashboard Cloudflare DNS Anda!

---

### Langkah 7: Jalankan Tunnel Sebagai Service Otomatis
Agar tunnel selalu aktif meskipun VPS di-restart, daftarkan sebagai systemd service:
```bash
sudo cloudflared service install
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
sudo systemctl status cloudflared
```

---

## ⚡ Opsi Alternatif Cepat (Quick Tunnel Tanpa Konfigurasi Domain)
Jika Anda hanya ingin uji coba cepat saat hari ujian tanpa mengubah DNS domain:
```bash
cloudflared tunnel --url http://localhost:80
```
Cloudflare akan memberikan tautan publik instan (misal: `https://contoh-random.trycloudflare.com`) yang bisa langsung dibagikan ke para penguji.

---

## 🔒 Konfigurasi Google Sheets di VPS
1. Buka domain yang sudah aktif di peramban (`https://ukk.domainanda.com`).
2. Masuk menggunakan akun admin:
   - **Username:** `admin`
   - **Password:** `adminukk2026`
3. Masuk ke tab **Pengaturan & Cloud**.
4. Paste isi file JSON Service Account Google Anda pada formulir yang tersedia dan klik **Terapkan Service Account**.
5. Pastikan email Service Account sudah di-share sebagai **Editor** pada Google Spreadsheet `1Ri7F8T7YTQdr7F71aslfVpIfYrSva_F0dmtbT5tBJW8`.

Selamat! Sistem Penilaian UKK Cloud Engineer SMK Negeri 1 Banyumas kini sudah online, profesional, dan siap digunakan.
