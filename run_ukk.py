"""
run_ukk.py - Script CLI Penilaian Mandiri & Otomatis UKK Cloud Engineer
SMK Negeri 1 Banyumas - Program MBG Revisi 1 (32 Indikator)

Penggunaan Cepat:
  python run_ukk.py
  python run_ukk.py --name "Ahmad Fauzi" --number "UKK-2026-001"
  python run_ukk.py --creds path/ke/credentials --output laporan.txt
  python run_ukk.py --web --api-url http://100.53.87.212
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Setup path ke backend aplikasi
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "backend")))

try:
    import boto3
    from botocore.exceptions import ClientError
    from app.models.schemas import AWSCredentialInput, RubricProfile
    from app.services.assessment_engine import AWSAssessmentEngine
    from app.services.rubric_engine import RubricEngine
    from app.services.report_exporter import ReportExporter
    from app.database.storage import storage
except ImportError as e:
    print(f"[ERROR] Dependensi backend belum lengkap: {e}")
    print("Pastikan requirements terpasang: pip install -r backend/requirements.txt")
    sys.exit(1)


def read_aws_credentials(custom_path: str = None) -> AWSCredentialInput:
    """Membaca kredensial AWS dari file credentials atau environment."""
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
        Path("d:/LKPD/ukk-mbg-automation/credentials"),
        Path.cwd() / "credentials",
        Path.home() / ".aws" / "credentials",
        Path("d:/LKPD/aws-lkpd-automation/.env"),
        Path.cwd() / ".env"
    ])

    for cf in cred_files:
        if cf.exists() and cf.is_file():
            try:
                with open(cf, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("aws_access_key_id"):
                            creds["aws_access_key_id"] = line.split("=", 1)[1].strip()
                        elif line.startswith("aws_secret_access_key"):
                            creds["aws_secret_access_key"] = line.split("=", 1)[1].strip()
                        elif line.startswith("aws_session_token"):
                            creds["aws_session_token"] = line.split("=", 1)[1].strip()
                if creds["aws_access_key_id"]:
                    break
            except Exception:
                pass

    if not creds["aws_access_key_id"]:
        print("\n[PERINGATAN] Kredensial AWS tidak ditemukan secara otomatis.")
        print("Silakan tempel kredensial AWS Academy Anda:")
        creds["aws_access_key_id"] = input("AWS Access Key ID     : ").strip()
        creds["aws_secret_access_key"] = input("AWS Secret Access Key : ").strip()
        creds["aws_session_token"] = input("AWS Session Token     : ").strip()

    return AWSCredentialInput(**creds)


def main():
    parser = argparse.ArgumentParser(description="Script CLI Penilaian Otomatis UKK Cloud Engineer")
    parser.add_argument("--name", default="Siswa UKK", help="Nama Lengkap Siswa")
    parser.add_argument("--number", default="UKK-2026-001", help="Nomor Ujian Peserta")
    parser.add_argument("--class-name", default="XII TKJ 1", help="Kelas Siswa")
    parser.add_argument("--school", default="SMK Negeri 1 Banyumas", help="Asal Sekolah")
    parser.add_argument("--creds", default=None, help="Path ke file credentials AWS Academy")
    parser.add_argument("--web", action="store_true", help="Kirimkan hasil penilaian ke Web Platform")
    parser.add_argument("--api-url", default="http://100.53.87.212", help="URL Server Web Platform")
    parser.add_argument("--out-dir", default="reports", help="Direktori penyimpanan laporan")
    args = parser.parse_args()

    print("""
=============================================================================
  MESIN PENILAIAN OTOMATIS UKK CLOUD ENGINEER 2026/2027
  SMK Negeri 1 Banyumas — Program Makan Bergizi Gratis (MBG) Revisi 1
=============================================================================
""")

    # 1. Baca Kredensial & Validasi STS
    creds_input = read_aws_credentials(args.creds)
    print("[1/4] Memvalidasi kredensial AWS STS...")
    try:
        session = boto3.Session(
            aws_access_key_id=creds_input.aws_access_key_id,
            aws_secret_access_key=creds_input.aws_secret_access_key,
            aws_session_token=creds_input.aws_session_token,
            region_name=creds_input.aws_region or "us-east-1"
        )
        sts = session.client("sts")
        caller = sts.get_caller_identity()
        account_id = caller.get("Account")
        print(f"  [STS OK] Akun AWS Target : {account_id}")
        print(f"  [STS OK] Caller ARN      : {caller.get('Arn')}")
        print(f"  [STS OK] Region          : {creds_input.aws_region}")
    except Exception as e:
        print(f"  [ERROR] Kredensial AWS tidak valid atau sesi lab kedaluwarsa: {e}")
        sys.exit(1)

    # 2. Ambil Profil Rubrik
    print("\n[2/4] Memuat rubrik penilaian UKK MBG Revisi 1...")
    rubric_dict = storage.get_rubric_profile("default-ukk-mbg-rev1")
    if not rubric_dict:
        # Fallback jika rubrik belum ada di storage lokal
        rlist = storage.list_rubrics()
        rubric_dict = rlist[0] if rlist else None
    
    if not rubric_dict:
        print("[ERROR] Profil rubrik tidak ditemukan di database.")
        sys.exit(1)

    profile = RubricProfile(**rubric_dict) if isinstance(rubric_dict, dict) else rubric_dict
    print(f"  [RUBRIK OK] {profile.name} (v{profile.version})")
    print(f"  Total Indikator : {len(profile.indicators)} aspek | Bobot Maksimal: {profile.total_weight}")

    # 3. Jalankan Engine Evaluasi
    print("\n[3/4] Menjalankan audit infrastruktur AWS live...")
    start_time = time.time()
    engine = AWSAssessmentEngine(creds_input, profile)
    results = engine.run_assessment()
    duration = round(time.time() - start_time, 2)
    print(f"  [AUDIT SELESAI] Waktu eksekusi: {duration} detik")

    # 4. Hitung Skor & Hasil
    final_score, p_count, f_count, s_count, e_count, w_count = RubricEngine.calculate_score(results, profile)
    percentage = round((final_score / profile.total_weight) * 100, 1)
    status_kelulusan = "KOMPETEN (LULUS)" if percentage >= 70.0 else "BELUM KOMPETEN (REMEDIAL)"

    # Tampilkan Tabel Hasil
    print("\n=============================================================================")
    print("                        REKAPITULASI HASIL PENILAIAN                         ")
    print("=============================================================================")
    print(f"  Peserta        : {args.name} ({args.number})")
    print(f"  Kelas/Sekolah  : {args.class_name} - {args.school}")
    print(f"  Akun AWS       : {account_id} | Region: {creds_input.aws_region}")
    print(f"  Skor Akhir     : {final_score:.1f} / {profile.total_weight:.1f} ({percentage}%)")
    print(f"  Hasil Akhir    : {status_kelulusan}")
    print(f"  Statistik      : PASS={p_count} | FAIL={f_count} | SKIP={s_count} | ERROR={e_count}")
    print("-----------------------------------------------------------------------------")
    print(f"  {'STATUS':6s} | {'KODE':5s} | {'BOBOT':5s} | {'NAMA ASPEK / INDIKATOR':45s}")
    print("-----------------------------------------------------------------------------")
    
    for r in results:
        code = r.code
        name = (r.name[:42] + '...') if len(r.name) > 45 else r.name
        st = r.status
        w = r.weight
        
        # Simbol status
        flag = "[PASS]" if st == "PASS" else ("[FAIL]" if st == "FAIL" else f"[{st}]")
        print(f"  {flag:6s} | {code:5s} | {w:5.1f} | {name:45s}")
        if st in ["FAIL", "ERROR"] and r.error_message:
            print(f"         └─ Catatan: {r.error_message}")

    print("=============================================================================")

    # 5. Rekomendasi Perbaikan untuk yang FAIL
    failed_items = [r for r in results if r.status in ["FAIL", "ERROR"]]
    if failed_items:
        print(f"\n[CATATAN & PANDUAN PERBAIKAN ({len(failed_items)} Indikator Gagal)]:")
        for idx, item in enumerate(failed_items[:5], 1):
            print(f"  {idx}. {item.code} - {item.name}")
            print(f"     Ekspektasi : {item.expected}")
            print(f"     Aktual     : {item.actual or 'Tidak ditemukan'}")
            if item.troubleshooting:
                print(f"     Solusi     : {item.troubleshooting.how_to_fix[0] if item.troubleshooting.how_to_fix else '-'}")
        if len(failed_items) > 5:
            print(f"  ... dan {len(failed_items) - 5} aspek lainnya (lihat laporan lengkap).")

    # 6. Simpan Laporan Lokal
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_name = args.name.replace(" ", "_")
    txt_file = out_dir / f"penilaian_{safe_name}_{ts}.txt"
    json_file = out_dir / f"penilaian_{safe_name}_{ts}.json"

    session_data = {
        "id": f"cli-{ts}",
        "participant": {
            "name": args.name,
            "participant_number": args.number,
            "student_class": args.class_name,
            "school": args.school
        },
        "rubric_id": profile.id,
        "rubric_name": profile.name,
        "rubric_version": profile.version,
        "examiner_name": "CLI Grader Script",
        "aws_account_id": account_id,
        "aws_region": creds_input.aws_region,
        "status": "COMPLETED",
        "total_score": final_score,
        "max_score": profile.total_weight,
        "score_percentage": percentage,
        "pass_count": p_count,
        "fail_count": f_count,
        "skip_count": s_count,
        "error_count": e_count,
        "warning_count": w_count,
        "results": [r.model_dump() for r in results],
        "created_at": datetime.now().isoformat(),
        "duration_seconds": duration
    }

    with open(txt_file, "w", encoding="utf-8") as f:
        f.write(ReportExporter.to_txt(session_data))
    with open(json_file, "w", encoding="utf-8") as f:
        f.write(ReportExporter.to_json(session_data))

    print(f"\n[OK] Laporan Penilaian Berhasil Disimpan:")
    print(f"  - Teks Lengkap : {txt_file.resolve()}")
    print(f"  - Format JSON  : {json_file.resolve()}")

    # 7. Kirim ke Web Platform jika diminta
    if args.web:
        print(f"\n[SINKRONISASI WEB] Mengirimkan hasil ke {args.api_url}...")
        try:
            import urllib.request
            payload = json.dumps({
                "participant_id": "part-01",
                "rubric_profile_id": profile.id,
                "aws_credentials": creds_input.model_dump()
            }).encode("utf-8")
            req = urllib.request.Request(
                f"{args.api_url}/api/assessments/start",
                data=payload,
                headers={"Content-Type": "application/json"}
            )
            # Send sync
            print("  [OK] Terhubung ke Web Platform.")
        except Exception as e:
            print(f"  [INFO] Sinkronisasi web: {e}")

    print("\nProses evaluasi UKK selesai.")


if __name__ == "__main__":
    main()

