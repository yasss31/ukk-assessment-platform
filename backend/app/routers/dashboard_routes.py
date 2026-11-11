"""
app/routers/dashboard_routes.py - Dashboard Metrik & Status Sistem
"""
from datetime import datetime
from fastapi import APIRouter, Depends
from app.auth import get_current_user
from app.models.schemas import User, ServiceHealthStatus
from app.database.storage import storage

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats")
async def get_dashboard_stats(current_user: User = Depends(get_current_user)):
    assessments = storage.list_assessments()
    participants = storage.list_participants()
    rubrics = storage.list_rubrics()
    autoplay = storage.get_autoplay_config()

    total_assessments = len(assessments)
    completed = [a for a in assessments if a.get("status") == "COMPLETED"]
    failed = [a for a in assessments if a.get("status") == "FAILED"]
    running = [a for a in assessments if a.get("status") == "RUNNING"]

    avg_score = 0.0
    pass_rate = 0.0
    if completed:
        avg_score = round(sum(a.get("total_score", 0.0) for a in completed) / len(completed), 1)
        passed = [a for a in completed if a.get("total_score", 0.0) >= (a.get("max_score", 100.0) * 0.7)]
        pass_rate = round((len(passed) / len(completed)) * 100, 1)

    sheets_status = storage.sheets.get_status()

    return {
        "total_participants": len(participants),
        "total_assessments": total_assessments,
        "completed_assessments": len(completed),
        "completed_count": len(completed),
        "failed_count": len(failed),
        "running_count": len(running),
        "average_score": avg_score,
        "pass_rate": pass_rate,
        "active_rubrics_count": len(rubrics),
        "auto_play": {
            "is_enabled": autoplay.get("is_enabled", False),
            "interval_minutes": autoplay.get("interval_minutes", 180),
            "last_status": autoplay.get("last_status", "DISABLED"),
            "next_run": autoplay.get("next_run")
        },
        "auto_play_enabled": autoplay.get("is_enabled", False),
        "google_sheets": sheets_status,
        "recent_assessments": assessments[:5]
    }


@router.get("/health", response_model=ServiceHealthStatus)
async def get_health_status():
    sheets_info = storage.sheets_service.get_status()
    autoplay = storage.get_autoplay_config()
    assessments = storage.list_assessments()
    running = len([a for a in assessments if a.get("status") == "RUNNING"])

    return ServiceHealthStatus(
        backend_status="HEALTHY",
        google_sheets_status=sheets_info["status"],
        storage_mode="sheets" if sheets_info["is_connected"] else "local_fallback",
        active_assessments_count=running,
        auto_play_status="ENABLED" if autoplay.get("is_enabled") else "DISABLED",
        timestamp=datetime.utcnow().isoformat()
    )

