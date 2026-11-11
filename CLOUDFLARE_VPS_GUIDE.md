# Panduan Menghubungkan Domain ke VPS Menggunakan Cloudflare Tunnel (`cloudflared`)

Panduan ini menjelaskan cara mempublikasikan **UKK Assessment Platform** yang berjalan di VPS Anda agar dapat diakses oleh para penguji melalui domain pribadi (misalnya `ukk.domainanda.com`) tanpa perlu membuka port router/firewall dan sudah otomatis mendapatkan sertifikat SSL HTTPS gratis dari Cloudflare.

---

## 🎯 Mengapa Menggunakan Cloudflare Tunnel?

1. **Tanpa Port Forwarding:** Anda tidak perlu membuka port 80/443 di firewall VPS Anda.
2. **IP VPS Tersembunyi:** IP publik VPS Anda aman dari serangan DDoS dan pemindaian port publik.
3. **SSL/HTTPS Otomatis:** Koneksi terenkripsi penuh tanpa perlu repot mengonfigurasi Let's Encrypt / Certbot.
4. **Otomatis Melalui Docker:** Container `cloudflared` sudah terintegrasi di `docker-compose.yml`.

---

## 🚀 Cara Cepat (Zero-Touch via Docker Compose)

Jika Anda sudah memiliki Cloudflare Tunnel Token, Anda cukup memasukkannya ke file `.env` di VPS:

1. Buat file `.env` di folder root `ukk-assessment-platform`:
   ```bash
   cp .env.example .env
   nano .env
   ```
2. Isi nilai `CLOUDFLARE_TUNNEL_TOKEN`:
   ```env
   CLOUDFLARE_TUNNEL_TOKEN=<MASUKKAN_TOKEN_CLOUDFLARE_TUNNEL_ANDA>
   ```

3. Jalankan container:
   ```bash
   docker compose up -d --build
   ```
   Layanan `cloudflared` akan otomatis menyala di background, terhubung ke Cloudflare Edge Network, dan merutekan traffic domain Anda ke container frontend (port 80).

---

## 📋 Cara Manual via `systemd` Service (Opsi Alternatif di Host VPS)

Jika ingin menjalankan `cloudflared` langsung di host OS VPS (bukan di Docker):

### Langkah 1: Pasang `cloudflared` di VPS
```bash
# Unduh binary resmi cloudflared (Linux x86_64)
curl -L --output cloudflared.deb https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb

# Pasang paket
sudo dpkg -i cloudflared.deb
```

### Langkah 2: Daftarkan Service Menggunakan Token Anda
Jalankan perintah instalasi service dengan token Anda:
```bash
sudo cloudflared service install <TOKEN_CLOUDFLARE_TUNNEL_ANDA>
```


### Langkah 3: Aktifkan Service
```bash
sudo systemctl enable cloudflared
sudo systemctl start cloudflared
sudo systemctl status cloudflared
```

---

## 🔒 Konfigurasi Google Sheets di VPS
1. Buka domain yang sudah aktif di peramban (`https://ukk.domainanda.com`).
2. Masuk menggunakan akun admin:
   - **Username:** `admin`
   - **Password:** `adminukk2026` *(Disarankan langsung diganti melalui ikon Kunci di pojok kanan atas)*
3. Masuk ke tab **Pengaturan & Cloud**.
4. Paste isi file JSON Service Account Google Anda pada formulir yang tersedia dan klik **Terapkan Service Account**.
5. Pastikan email Service Account sudah di-share sebagai **Editor** pada Google Spreadsheet `1Ri7F8T7YTQdr7F71aslfVpIfYrSva_F0dmtbT5tBJW8`.

Selamat! Sistem Penilaian UKK Cloud Engineer SMK Negeri 1 Banyumas kini sudah online, profesional, dan siap digunakan.
