"""
run_autoplay.py - Script CLI Kontrol & Eksekusi AWS Auto Play
UKK Assessment Platform - SMK Negeri 1 Banyumas

Fungsi Auto Play:
  Secara berkala memantau instance EC2 target (misal mbg-ec2-* pada AWS Learner Lab)
  dan menyalakan kembali (StartInstances) secara otomatis jika instance dalam keadaan 'stopped'.
  Idempotent: Jika sudah 'running', tidak akan melakukan tindakan apa pun.

Cara Penggunaan:
  1. Cek status & konfigurasi saat ini:
     python run_autoplay.py --status

  2. Jalankan 1 siklus pemeriksaan sekarang:
     python run_autoplay.py --run-now

  3. Aktifkan jadwal Auto Play (misal tiap 180 menit / 3 jam):
     python run_autoplay.py --enable --interval 180

  4. Matikan Auto Play:
     python run_autoplay.py --disable

  5. Jalankan daemon pemantau terus-menerus (loop di background/terminal):
     python run_autoplay.py --loop --interval 180
"""

import argparse
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Setup path ke backend aplikasi
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

try:
    import boto3
    from botocore.exceptions import ClientError
    from app.models.schemas import AWSCredentialInput
    from app.services.auto_play_manager import AWSAutoPlayManager
    from app.database.storage import storage
except ImportError as e:
    print(f"[ERROR] Dependensi backend belum lengkap: {e}")
    print("Pastikan requirements terpasang: pip install -r backend/requirements.txt")
    sys.exit(1)


def read_aws_credentials(custom_path: str = None) -> AWSCredentialInput:
    """Membaca kredensial AWS Academy dari file credentials, .env, atau environment."""
    creds = {
        "aws_access_key_id": os.getenv("AWS_ACCESS_KEY_ID", ""),
        "aws_secret_access_key": os.getenv("AWS_SECRET_ACCESS_KEY", ""),
        "aws_session_token": os.getenv("AWS_SESSION_TOKEN", ""),
        "aws_region": os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    }

    cred_files = []
    if custom_path:
        cred_files.append(Path(custom_path))
    cred_files.extend([
        Path.home() / ".aws" / "credentials",
        Path("d:/LKPD/aws-lkpd-automation/.env"),
        Path.cwd() / ".env"
    ])

    for cf in cred_files:
        if cf.is_file():
            try:
                content = cf.read_text(encoding="utf-8", errors="ignore")
                for line in content.splitlines():
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip().upper()
                        v = v.strip().strip("'\"")
                        if "AWS_ACCESS_KEY_ID" in k and not creds["aws_access_key_id"]:
                            creds["aws_access_key_id"] = v
                        elif "AWS_SECRET_ACCESS_KEY" in k and not creds["aws_secret_access_key"]:
                            creds["aws_secret_access_key"] = v
                        elif "AWS_SESSION_TOKEN" in k and not creds["aws_session_token"]:
                            creds["aws_session_token"] = v
                        elif "AWS_DEFAULT_REGION" in k or "AWS_REGION" in k:
                            creds["aws_region"] = v
                if creds["aws_access_key_id"] and creds["aws_secret_access_key"]:
                    break
            except Exception:
                pass

    return AWSCredentialInput(**creds)


def print_status():
    """Tampilkan status konfigurasi dan riwayat log Auto Play."""
    cfg = storage.get_autoplay_config()
    print("=" * 65)
    print("          STATUS AWS AUTO PLAY - UKK ASSESSMENT")
    print("=" * 65)
    is_enabled = cfg.get("is_enabled", False)
    status_str = "AKTIF (ENABLED) [ON]" if is_enabled else "NONAKTIF (DISABLED) [OFF]"
    print(f"Status Auto Play     : {status_str}")
    print(f"Interval Pemantauan  : {cfg.get('interval_minutes', 180)} Menit")
    print(f"Terakhir Dijalankan  : {cfg.get('last_run', 'Belum pernah')}")
    print(f"Jadwal Berikutnya    : {cfg.get('next_run', 'Tidak ada jadwal aktif')}")
    print(f"Status Terakhir      : {cfg.get('last_status', 'N/A')}")
    if cfg.get("last_error"):
        print(f"Pesan Error Terakhir : {cfg.get('last_error')}")
    
    targets = cfg.get("target_instances", [])
    if targets:
        print(f"Allowlist Target EC2 : {len(targets)} instance terdaftar")
        for t in targets:
            print(f"  - {t.get('instance_id')} ({t.get('name', 'Tanpa Nama')})")
    else:
        print("Allowlist Target EC2 : [Auto-Discover] Semua instance dengan tag 'mbg-ec2-*'")
    print("-" * 65)

    logs = storage.get_autoplay_logs(limit=5)
    print("5 Log Aktivitas Terakhir:")
    if not logs:
        print("  (Belum ada riwayat aktivitas log)")
    else:
        for idx, l in enumerate(logs, 1):
            ts = l.get("timestamp", "")[:19].replace("T", " ")
            action = l.get("action", "")
            stat = l.get("status", "")
            detail = l.get("details", "")
            print(f"  [{ts}] [{stat}] {action}: {detail}")
    print("=" * 65)


def run_cycle_now(creds: AWSCredentialInput):
    """Jalankan satu siklus pemeriksaan dan nyalakan instance secara langsung."""
    print("=" * 65)
    print("           MENJALANKAN 1 SIKLUS AWS AUTO PLAY")
    print("=" * 65)
    print(f"Region : {creds.aws_region or 'us-east-1'}")
    
    # Pastikan status sementara aktif agar lolos validasi manager
    cfg = storage.get_autoplay_config()
    was_disabled = not cfg.get("is_enabled")
    if was_disabled:
        cfg["is_enabled"] = True
        storage.save_autoplay_config(cfg)

    try:
        print("Memeriksa status EC2 target di AWS...")
        result = AWSAutoPlayManager.run_auto_play_cycle(creds)
        print("-" * 65)
        print(f"Hasil Eksekusi : {result.get('status')}")
        if result.get("status") == "SUCCESS":
            print(f"Pesan          : {result.get('message')}")
            print(f"Instance Dinyalakan : {result.get('started_count', 0)}")
            print(f"Instance Berjalan   : {result.get('running_count', 0)}")
        else:
            print(f"Detail/Error   : {result.get('error') or result.get('message')}")
    finally:
        # Kembalikan status jika sebelumnya memang dinonaktifkan
        if was_disabled:
            cfg["is_enabled"] = False
            storage.save_autoplay_config(cfg)
    print("=" * 65)


def run_continuous_loop(creds: AWSCredentialInput, interval_minutes: int):
    """Menjalankan loop pemantau berkala."""
    print("=" * 65)
    print(f"   MEMULAI DAEMON PEMANTAU AUTO PLAY (Setiap {interval_minutes} Menit)")
    print("   Tekan Ctrl+C untuk menghentikan daemon.")
    print("=" * 65)
    
    # Set config menjadi enabled
    AWSAutoPlayManager.update_config(is_enabled=True, interval_minutes=interval_minutes)

    try:
        while True:
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(f"\n[{now_str}] Menjalankan siklus pemantauan...")
            result = AWSAutoPlayManager.run_auto_play_cycle(creds)
            print(f"Hasil: {result.get('status')} - {result.get('message', result.get('error'))}")
            
            wait_seconds = interval_minutes * 60
            print(f"Menunggu {interval_minutes} menit ({wait_seconds}s) hingga pengecekan berikutnya...")
            time.sleep(wait_seconds)
    except KeyboardInterrupt:
        print("\n[INFO] Daemon Auto Play dihentikan oleh pengguna.")


def main():
    parser = argparse.ArgumentParser(description="Script CLI Kontrol AWS Auto Play UKK Assessment")
    parser.add_argument("--status", action="store_true", help="Tampilkan status konfigurasi dan riwayat log")
    parser.add_argument("--run-now", action="store_true", help="Jalankan 1 siklus pengecekan dan start instance sekarang")
    parser.add_argument("--enable", action="store_true", help="Aktifkan Auto Play")
    parser.add_argument("--disable", action="store_true", help="Nonaktifkan Auto Play")
    parser.add_argument("--interval", type=int, default=180, help="Interval pemantauan dalam menit (default: 180)")
    parser.add_argument("--loop", action="store_true", help="Jalankan pemantau loop secara terus menerus di terminal")
    parser.add_argument("--creds", type=str, default=None, help="Path ke file credentials AWS kustom")

    args = parser.parse_args()

    # Jika tanpa argumen, default tampilkan status dan bantuan
    if not any([args.status, args.run_now, args.enable, args.disable, args.loop]):
        print_status()
        print("\nTips Perintah:")
        print("  python run_autoplay.py --run-now         (Jalankan 1x sekarang)")
        print("  python run_autoplay.py --enable --interval 180")
        print("  python run_autoplay.py --disable")
        print("  python run_autoplay.py --loop            (Jalankan terus di terminal)")
        return

    if args.status:
        print_status()
        return

    if args.enable:
        cfg = AWSAutoPlayManager.update_config(is_enabled=True, interval_minutes=args.interval)
        print(f"[OK] Auto Play BERHASIL DIAKTIFKAN dengan interval {cfg.interval_minutes} menit.")
        print(f"Jadwal berikutnya: {cfg.next_run}")
        return

    if args.disable:
        cfg = AWSAutoPlayManager.update_config(is_enabled=False)
        print("[OK] Auto Play BERHASIL DINONAKTIFKAN.")
        return

    creds = read_aws_credentials(args.creds)
    if not creds.aws_access_key_id or not creds.aws_secret_access_key:
        print("[PERINGATAN] Kredensial AWS tidak ditemukan secara otomatis.")
        print("Masukkan kredensial AWS Academy kamu secara manual:")
        creds.aws_access_key_id = input("AWS Access Key ID     : ").strip()
        creds.aws_secret_access_key = input("AWS Secret Access Key : ").strip()
        creds.aws_session_token = input("AWS Session Token (opsional jika bukan Academy): ").strip() or None

    if args.run_now:
        run_cycle_now(creds)
        return

    if args.loop:
        run_continuous_loop(creds, args.interval)
        return


if __name__ == "__main__":
    main()
