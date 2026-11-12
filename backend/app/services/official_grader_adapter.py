"""
app/services/official_grader_adapter.py - Adapter Resmi Penilaian UKK Cloud Engineer
SINGLE SOURCE OF TRUTH: grade.py & Soal_UKK Cloud Engineer_2627-Rev1.pdf
"""
import os
import sys
import json
import time
import uuid
import tempfile
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.models.schemas import (
    AWSCredentialInput, IndicatorResult, IndicatorStatus, ErrorSeverity,
    TroubleshootingGuide, AssessmentSession, AssessmentStatus, Participant
)
from app.services.official_rubric_kb import OFFICIAL_ASPEK_METADATA


class OfficialGraderAdapter:
    """
    Menghubungkan official grader `grade.py` langsung ke UKK Assessment Platform.
    Memastikan rumus skor, bobot 17 aspek (188 indikator evaluasi), dan kriteria PASS/FAIL
    100% identik dengan hasil grader resmi penguji.
    """

    @classmethod
    def run_assessment(
        cls,
        creds: AWSCredentialInput,
        participant: Participant,
        examiner_name: str = "Penguji Resmi UKK",
        test_asg: bool = False,
        skip_sns_wait: bool = True
    ) -> AssessmentSession:
        session_id = f"sess-{uuid.uuid4().hex[:12]}"
        started_at = datetime.utcnow().isoformat()
        
        # 1. Siapkan file credentials sementara untuk dieksekusi oleh grade.py
        temp_dir = tempfile.mkdtemp()
        cred_file = Path(temp_dir) / "credentials"
        cred_content = (
            f"[default]\n"
            f"aws_access_key_id = {creds.aws_access_key_id}\n"
            f"aws_secret_access_key = {creds.aws_secret_access_key}\n"
            f"aws_session_token = {creds.aws_session_token or ''}\n"
        )
        cred_file.write_text(cred_content, encoding="utf-8")

        # 2. Temukan path grade.py resmi (prioritas lokal container, repo platform, dan folder kerja)
        base_dir = Path(__file__).resolve().parent.parent.parent
        grade_py_paths = [
            base_dir / "grade.py",
            Path("/app/grade.py"),
            Path("D:/LKPD/ukk-mbg-automation/grade.py"),
            Path("D:/LKPD/grade.py"),
            Path.cwd() / "grade.py",
            Path.cwd().parent / "grade.py"
        ]
        grade_script = next((p for p in grade_py_paths if p.is_file()), None)
        if not grade_script:
            raise FileNotFoundError("Script resmi grade.py tidak ditemukan di sistem.")

        # 3. Jalankan grade.py secara tersinkronisasi
        out_dir = Path(temp_dir) / "reports"
        out_dir.mkdir(parents=True, exist_ok=True)

        cmd = [
            sys.executable,
            str(grade_script),
            "--credentials", str(cred_file),
            "--out", str(out_dir),
            "--nama", participant.name or "Peserta",
            "--password", "123"
        ]
        if skip_sns_wait:
            cmd.append("--skip-sns-wait")
        if test_asg:
            cmd.append("--test-asg")

        start_time = time.time()
        # Isolasi kredensial lingkungan agar kredensial host EC2 tidak tertukar
        env = os.environ.copy()
        env["AWS_SHARED_CREDENTIALS_FILE"] = str(cred_file)
        env["AWS_DEFAULT_REGION"] = creds.aws_region or "us-east-1"
        env["AWS_REGION"] = creds.aws_region or "us-east-1"
        env.pop("AWS_ACCESS_KEY_ID", None)
        env.pop("AWS_SECRET_ACCESS_KEY", None)
        env.pop("AWS_SESSION_TOKEN", None)
        env.pop("AWS_PROFILE", None)
        env["PYTHONIOENCODING"] = "utf-8"

        proc = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            env=env
        )
        duration = round(time.time() - start_time, 2)

        # 4. Cari berkas json hasil evaluasi grade.py
        report_files = list(out_dir.glob("hasil_penilaian_*.json"))
        if not report_files:
            # Jika eksekusi gagal total
            err_msg = proc.stderr or proc.stdout or "Gagal mengeksekusi grade.py"
            session = AssessmentSession(
                id=session_id,
                participant=participant,
                rubric_id="RUBRIC-UKK-REV1-OFFICIAL",
                rubric_name="UKK Cloud Engineer 2026/2027 - Revisi 1 (grade.py Resmi)",
                rubric_version="1.0-official",
                examiner_name=examiner_name,
                aws_region=creds.aws_region or "us-east-1",
                status=AssessmentStatus.FAILED,
                total_score=0.0,
                notes=f"Eksekusi grader gagal: {err_msg[:300]}",
                started_at=started_at,
                completed_at=datetime.utcnow().isoformat(),
                duration_seconds=duration
            )
            return session

        latest_json = sorted(report_files, key=lambda f: f.stat().st_mtime)[-1]
        data = json.loads(latest_json.read_text(encoding="utf-8"))

        # 5. Transformasi hasil 17 aspek & sub-indikator resmi ke schema platform
        results: List[IndicatorResult] = []
        pass_count = 0
        fail_count = 0
        skip_count = 0
        warning_count = 0
        error_count = 0

        aspek_dict = data.get("aspek", {})
        final_score = float(data.get("nilai_akhir", 0.0))
        account_id = data.get("akun")

        for key in sorted(aspek_dict.keys()):
            asp = aspek_dict[key]
            title = asp.get("judul", f"Aspek {key}")
            bobot = float(asp.get("bobot", 0.0))
            is_skipped = asp.get("skip") is not None
            ratio = float(asp.get("rasio", 0.0)) if not is_skipped else None
            checks = asp.get("checks", [])

            # Meta referensi dokumen dari knowledge base
            meta = OFFICIAL_ASPEK_METADATA.get(key, {})

            # Hitung sub-checks status
            failed_subchecks = [c for c in checks if c.get("status") == "FAIL"]
            passed_subchecks = [c for c in checks if c.get("status") == "PASS"]
            info_subchecks = [c for c in checks if c.get("status") == "WARN"]

            evidence_lines = []
            for c in checks:
                st = c.get("status", "INFO")
                desc = c.get("desc", "")
                dt = c.get("detail", "")
                evidence_lines.append(f"[{st}] {desc}" + (f" -> {dt}" if dt else ""))
            evidence_str = "\n".join(evidence_lines)

            # Tentukan status utama
            if is_skipped:
                ind_status = IndicatorStatus.SKIP
                skip_count += 1
                score_earned = 0.0
                actual_text = f"DILEWATI (SKIP): {asp.get('skip')}"
                evidence_str = f"[SKIP] {asp.get('skip')}"
            elif ratio == 1.0:
                ind_status = IndicatorStatus.PASS
                pass_count += 1
                score_earned = bobot
                actual_text = f"{len(passed_subchecks)}/{len(checks)} check PASS ({score_earned:.1f}/{bobot:.1f} poin)"
            elif ratio == 0.0:
                ind_status = IndicatorStatus.FAIL
                fail_count += 1
                score_earned = 0.0
                actual_text = f"{len(passed_subchecks)}/{len(checks)} check PASS ({score_earned:.1f}/{bobot:.1f} poin)"
            else:
                # Sebagian lulus sebagian gagal
                ind_status = IndicatorStatus.WARNING
                warning_count += 1
                score_earned = round(bobot * ratio, 2)
                actual_text = f"{len(passed_subchecks)}/{len(checks)} check PASS ({score_earned:.1f}/{bobot:.1f} poin)"

            # Tentukan severity
            if is_skipped:
                severity = ErrorSeverity.INFORMATIONAL
            elif ind_status == IndicatorStatus.FAIL:
                severity = ErrorSeverity.CRITICAL if bobot >= 6.0 else ErrorSeverity.MAJOR
            elif ind_status == IndicatorStatus.WARNING:
                severity = ErrorSeverity.MAJOR
            else:
                severity = ErrorSeverity.INFORMATIONAL

            # Susun Troubleshooting Guide ramah siswa berpedoman pada UKK Rev1
            if is_skipped:
                what_is_wrong = f"Aspek ini dilewati ({asp.get('skip')}). Pengujian ini opsional dan tidak mengurangi skor kelulusan."
                actual_found = str(asp.get("skip"))
            elif failed_subchecks:
                what_is_wrong = f"Ditemukan {len(failed_subchecks)} dari {len(checks)} pemeriksaan belum sesuai spesifikasi resmi."
                actual_found = "; ".join([f"{c['desc']}: {c.get('detail', 'gagal')}" for c in failed_subchecks[:3]])
            else:
                what_is_wrong = "Konfigurasi dan pengujian aspek ini sudah sesuai spesifikasi."
                actual_found = f"{len(passed_subchecks)} dari {len(checks)} pemeriksaan lulus (PASS)."

            troubleshooting = TroubleshootingGuide(
                severity=severity,
                what_is_wrong=what_is_wrong,
                actual_found=actual_found,
                expected_config=meta.get("expected_condition", "Konfigurasi sesuai Bab C & Bab D Dokumen Soal UKK Rev1."),
                why_wrong=f"Ketidaksesuaian pada {title} dapat mengganggu fungsi atau integrasi infrastruktur cloud MBG.",
                impact="Penilaian aspek ini tidak mendapatkan nilai penuh atau fungsi aplikasi tidak dapat diverifikasi.",
                fix_location=f"Dokumen UKK Rev1: {meta.get('doc_chapter', 'Bab C & D')} | {meta.get('doc_pages', 'Halaman terkait')}",
                how_to_fix=meta.get("troubleshooting_steps", [
                    f"Buka panduan {meta.get('doc_name', 'Soal UKK Rev1')} bagian {meta.get('doc_chapter', '')}.",
                    f"Ikuti langkah pengerjaan pada {meta.get('doc_procedure', 'prosedur terkait')}.",
                    "Periksa kembali parameter penamaan, CIDR, security group, dan konfigurasi layanan."
                ]),
                how_to_verify=meta.get("verification_steps", [
                    f"Jalankan verifikasi: {meta.get('cli_command', 'aws cli verify')}"
                ]),
                cli_guide=f"# Perintah Verifikasi ({meta.get('doc_chapter', '')}):\n{meta.get('cli_command', '')}\n# Hasil yang Diharapkan:\n{meta.get('expected_output', '')}"
            )

            res = IndicatorResult(
                indicator_id=f"IND-OFFICIAL-{key}",
                code=f"ASPEK-{key}",
                name=title,
                category=meta.get("category", "General"),
                expected=meta.get("expected_condition", "Sesuai spesifikasi resmi"),
                actual=actual_text,
                status=ind_status,
                score=score_earned,
                weight=bobot,
                evidence=evidence_str,
                severity=severity,
                troubleshooting=troubleshooting,
                is_resolved=(ind_status in [IndicatorStatus.PASS, IndicatorStatus.SKIP])
            )
            results.append(res)

        session = AssessmentSession(
            id=session_id,
            participant=participant,
            rubric_id="RUBRIC-UKK-REV1-OFFICIAL",
            rubric_name="UKK Cloud Engineer 2026/2027 - Revisi 1 (Single Source of Truth: grade.py)",
            rubric_version="1.0-official",
            examiner_name=examiner_name,
            aws_account_id=account_id,
            aws_region=creds.aws_region or "us-east-1",
            status=AssessmentStatus.COMPLETED,
            total_score=final_score,
            max_score=100.0,
            pass_count=pass_count,
            fail_count=fail_count,
            skip_count=skip_count,
            error_count=error_count,
            warning_count=warning_count,
            completion_percentage=100.0,
            results=results,
            notes=f"Penilaian resmi via grade.py selesai dalam {duration}s. Single source of truth grade.py & Soal_UKK Cloud Engineer_2627-Rev1.pdf.",
            started_at=started_at,
            completed_at=datetime.utcnow().isoformat(),
            duration_seconds=duration
        )

        # Cleanup temp directory
        try:
            cred_file.unlink(missing_ok=True)
            for f in out_dir.glob("*"):
                f.unlink(missing_ok=True)
            out_dir.rmdir()
            Path(temp_dir).rmdir()
        except Exception:
            pass

        return session

