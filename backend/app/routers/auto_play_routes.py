"""
app/routers/auto_play_routes.py - API Kontrol & Monitoring Auto Play
"""
from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from app.models.schemas import AutoPlayConfig, AutoPlayLog, AWSCredentialInput, User
from app.auth import get_current_user, require_examiner
from app.services.auto_play_manager import AWSAutoPlayManager
from app.database.storage import storage

router = APIRouter(prefix="/api/auto-play", tags=["AWS Auto Play"])


class UpdateAutoPlayRequest(BaseModel):
    is_enabled: bool
    interval_minutes: int = 180
    target_instances: Optional[List[Dict[str, Any]]] = None


class RunAutoPlayRequest(BaseModel):
    credentials: AWSCredentialInput


@router.get("/config", response_model=AutoPlayConfig)
def get_auto_play_config(current_user: User = Depends(require_examiner)):
    """Mendapatkan konfigurasi Auto Play saat ini."""
    return AWSAutoPlayManager.get_config()


@router.put("/config", response_model=AutoPlayConfig)
def update_auto_play_config(data: UpdateAutoPlayRequest, current_user: User = Depends(require_examiner)):
    """Memperbarui status aktif/nonaktif dan interval waktu Auto Play."""
    return AWSAutoPlayManager.update_config(
        is_enabled=data.is_enabled,
        interval_minutes=data.interval_minutes,
        target_instances=data.target_instances
    )


@router.post("/run-now")
def trigger_auto_play_now(data: RunAutoPlayRequest, current_user: User = Depends(require_examiner)):
    """Memicu 1 siklus pengecekan dan start instance yang stopped secara manual seketika."""
    result = AWSAutoPlayManager.run_auto_play_cycle(data.credentials)
    return result


@router.get("/logs")
def get_auto_play_logs(limit: int = 50, current_user: User = Depends(require_examiner)):
    """Mengambil riwayat log aktivitas Auto Play."""
    logs = storage.get_autoplay_logs(limit=limit)
    return {"logs": logs, "total": len(logs)}

