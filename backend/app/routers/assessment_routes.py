"""
app/routers/assessment_routes.py - Endpoint Penilaian AWS, Pelaporan, Reassessment, & Smart Feedback
"""
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Response, BackgroundTasks
from app.auth import get_current_user
from app.models.schemas import (
    User, AWSCredentialInput, AWSCredentialValidationResult,
    AssessmentCreate, AssessmentSession, AssessmentStatus, RubricProfile,
    IndicatorResult, ReassessmentRequest
)
from app.database.storage import storage
from app.services.aws_validator import AWSValidator
from app.services.assessment_engine import AWSAssessmentEngine
from app.services.rubric_engine import RubricEngine
from app.services.report_exporter import ReportExporter
from app.services.troubleshooting_kb import TroubleshootingKB

router = APIRouter(prefix="/api/assessments", tags=["Assessments"])


@router.post("/validate-aws", response_model=AWSCredentialValidationResult)
async def validate_aws_credentials(creds: AWSCredentialInput, current_user: User = Depends(get_current_user)):
    """Memvalidasi kredensial AWS STS secara instan tanpa menyimpannya."""
    return AWSValidator.validate_credentials(creds)


def _execute_assessment_task(session_id: str, creds: AWSCredentialInput, profile_dict: Any):
    """Worker fungsi eksekusi penilaian AWS di background."""
    if isinstance(profile_dict, dict):
        profile = RubricProfile(**profile_dict)
    else:
        profile = profile_dict

    session_data = storage.get_assessment(session_id)
    if not session_data:
        return

    session_data["status"] = AssessmentStatus.RUNNING.value
    storage.save_assessment(session_data)

    start_time = datetime.utcnow()
    try:
        engine = AWSAssessmentEngine(creds, profile)
        eval_results = engine.run_assessment()

        # Hitung skor akhir dengan RubricEngine
        final_score, p_count, f_count, s_count, e_count, w_count = RubricEngine.calculate_score(eval_results, profile)

        duration = (datetime.utcnow() - start_time).total_seconds()
        
        session_data["status"] = AssessmentStatus.COMPLETED.value
        session_data["total_score"] = final_score
        session_data["pass_count"] = p_count
        session_data["fail_count"] = f_count
        session_data["skip_count"] = s_count
        session_data["error_count"] = e_count
        session_data["warning_count"] = w_count
        session_data["completion_percentage"] = 100.0
        session_data["results"] = [
            r.model_dump() if hasattr(r, "model_dump") else r.dict()
            for r in eval_results
        ]
        session_data["completed_at"] = datetime.utcnow().isoformat()
        session_data["duration_seconds"] = round(duration, 1)

    except Exception as e:
        session_data["status"] = AssessmentStatus.FAILED.value
        session_data["notes"] = f"Kesalahan saat evaluasi AWS: {str(e)}"
        session_data["completed_at"] = datetime.utcnow().isoformat()

    storage.save_assessment(session_data)


@router.post("", status_code=201)
@router.post("/start", status_code=201)
async def start_assessment(payload: AssessmentCreate, background_tasks: BackgroundTasks, current_user: User = Depends(get_current_user)):
    """Memulai sesi penilaian baru dengan validasi kredensial AWS instan."""
    # 1. Validasi kredensial terlebih dahulu
    val = AWSValidator.validate_credentials(payload.aws_credentials)
    if not val.is_valid:
        raise HTTPException(status_code=400, detail=val.error_message or "Kredensial AWS tidak valid")

    # 2. Ambil profil rubrik dan peserta
    profile = storage.get_rubric_profile(payload.rubric_profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profil rubrik tidak ditemukan")

    participant = storage.get_participant(payload.participant_id)
    if not participant:
        raise HTTPException(status_code=404, detail="Peserta tidak ditemukan")

    p_dict = participant.model_dump() if hasattr(participant, "model_dump") else (participant.dict() if hasattr(participant, "dict") else participant)
    prof_dict = profile.model_dump() if hasattr(profile, "model_dump") else (profile.dict() if hasattr(profile, "dict") else profile)

    # 3. Buat sesi penilaian baru
    session_id = f"asm-{uuid.uuid4().hex[:10]}"
    new_session = {
        "id": session_id,
        "participant": p_dict,
        "rubric_id": prof_dict["id"],
        "rubric_name": prof_dict["name"],
        "rubric_version": prof_dict.get("version", "1.0"),
        "examiner_name": current_user.full_name,
        "aws_account_id": val.account_id,
        "aws_region": val.region,
        "status": AssessmentStatus.PENDING.value,
        "total_score": 0.0,
        "max_score": prof_dict.get("total_weight", 100.0),
        "pass_count": 0,
        "fail_count": 0,
        "skip_count": 0,
        "error_count": 0,
        "warning_count": 0,
        "completion_percentage": 0.0,
        "results": [],
        "notes": payload.notes,
        "started_at": datetime.utcnow().isoformat(),
        "completed_at": None,
        "duration_seconds": None
    }
    storage.save_assessment(new_session)

    # 4. Jalankan assessment worker di background task
    background_tasks.add_task(_execute_assessment_task, session_id, payload.aws_credentials, prof_dict)

    return {
        "id": session_id,
        "assessment_id": session_id,
        "status": "QUEUED",
        "account_id": val.account_id,
        "message": "Sesi penilaian telah dibuat dan sedang berjalan di latar belakang."
    }


@router.post("/{assessment_id}/reassess")
async def reassess_assessment(assessment_id: str, payload: ReassessmentRequest, current_user: User = Depends(get_current_user)):
    """
    Melakukan pemeriksaan ulang (Reassessment) terhadap indikator yang gagal atau dipilih,
    tanpa menghapus riwayat penilaian sebelumnya.
    """
    session_data = storage.get_assessment(assessment_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Sesi penilaian tidak ditemukan")

    val = AWSValidator.validate_credentials(payload.aws_credentials)
    if not val.is_valid:
        raise HTTPException(status_code=400, detail=val.error_message or "Kredensial AWS tidak valid")

    profile_id = session_data.get("rubric_id", "default-ukk-mbg-rev1")
    profile = storage.get_rubric_profile(profile_id)
    if not profile:
        profile = storage.get_rubric_profile("default-ukk-mbg-rev1")

    # Siapkan existing IndicatorResult objects
    existing_results = [
        IndicatorResult(**r) if isinstance(r, dict) else r
        for r in session_data.get("results", [])
    ]

    engine = AWSAssessmentEngine(payload.aws_credentials, profile)
    updated_results = engine.reassess_indicators(payload.indicator_ids, existing_results)

    # Hitung ulang skor terbobot
    final_score, p_count, f_count, s_count, e_count, w_count = RubricEngine.calculate_score(updated_results, profile)

    session_data["total_score"] = final_score
    session_data["pass_count"] = p_count
    session_data["fail_count"] = f_count
    session_data["skip_count"] = s_count
    session_data["error_count"] = e_count
    session_data["warning_count"] = w_count
    session_data["results"] = [
        r.model_dump() if hasattr(r, "model_dump") else r.dict()
        for r in updated_results
    ]
    session_data["notes"] = f"{session_data.get('notes', '')} [Pemeriksaan ulang pada {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}]".strip()
    storage.save_assessment(session_data)

    return {
        "status": "SUCCESS",
        "message": "Pemeriksaan ulang selesai.",
        "session": session_data
    }


@router.post("/{assessment_id}/indicators/{indicator_id}/ai-explain")
async def ai_explain_indicator(assessment_id: str, indicator_id: str, current_user: User = Depends(get_current_user)):
    """
    AI-assisted explanation engine: Menyederhanakan penjelasan kesalahan dan memberikan
    jawaban kontekstual berdasarkan hasil pemeriksaan nyata tanpa mengubah penilaian.
    """
    session_data = storage.get_assessment(assessment_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Sesi penilaian tidak ditemukan")

    results = session_data.get("results", [])
    matched_ind = next((r for r in results if r.get("indicator_id") == indicator_id or r.get("code") == indicator_id), None)
    if not matched_ind:
        raise HTTPException(status_code=404, detail="Indikator tidak ditemukan dalam sesi penilaian ini")

    code = matched_ind.get("code", "")
    expected = matched_ind.get("expected", "")
    actual = matched_ind.get("actual", "")
    guide = TroubleshootingKB.get_guide(code, expected, actual, matched_ind.get("error_message"))

    # Response AI terstruktur
    explanation = {
        "code": code,
        "name": matched_ind.get("name"),
        "status": matched_ind.get("status"),
        "severity": guide.severity,
        "ringkasan_ramah_siswa": f"Halo {session_data.get('participant', {}).get('name', 'Siswa')}, pada aspek {matched_ind.get('name')}, sistem mendeteksi bahwa {guide.what_is_wrong.lower()}",
        "kenapa_penting": guide.why_wrong,
        "dampak_nyata": guide.impact,
        "lokasi_menu": guide.fix_location,
        "panduan_perbaikan": guide.how_to_fix,
        "cara_verifikasi": guide.how_to_verify,
        "tips_sukses": "Setelah melakukan langkah di atas pada AWS Console, kamu dapat menekan tombol 'Periksa Ulang' pada halaman ini untuk memperbarui nilaimu seketika!"
    }
    return explanation


@router.get("")
async def list_assessments(current_user: User = Depends(get_current_user)):
    return storage.list_assessments()


@router.get("/{assessment_id}")
async def get_assessment(assessment_id: str, current_user: User = Depends(get_current_user)):
    res = storage.get_assessment(assessment_id)
    if not res:
        raise HTTPException(status_code=404, detail="Sesi penilaian tidak ditemukan")
    return res


@router.get("/{assessment_id}/export/{format_type}")
async def export_report(assessment_id: str, format_type: str, current_user: User = Depends(get_current_user)):
    session_data = storage.get_assessment(assessment_id)
    if not session_data:
        raise HTTPException(status_code=404, detail="Sesi penilaian tidak ditemukan")

    fmt = format_type.lower()
    if fmt == "json":
        content = ReportExporter.to_json(session_data)
        return Response(content=content, media_type="application/json", headers={"Content-Disposition": f"attachment; filename=penilaian_{assessment_id}.json"})
    elif fmt == "csv":
        content = ReportExporter.to_csv(session_data)
        return Response(content=content, media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=penilaian_{assessment_id}.csv"})
    elif fmt in ["html", "pdf"]:
        content = ReportExporter.to_html(session_data)
        return Response(content=content, media_type="text/html")
    else:
        raise HTTPException(status_code=400, detail="Format tidak didukung (gunakan 'json', 'csv', atau 'html')")
