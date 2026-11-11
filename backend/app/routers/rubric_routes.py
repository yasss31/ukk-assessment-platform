"""
app/routers/rubric_routes.py - API Manajemen Rubrik Dinamis
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from app.models.schemas import RubricProfile, RubricProfileCreate, RubricIndicator, User
from app.auth import get_current_user, require_examiner
from app.database.storage import storage
import uuid
from datetime import datetime

router = APIRouter(prefix="/api/rubrics", tags=["Rubrik Penilaian"])


@router.get("", response_model=List[RubricProfile])
def list_rubrics(current_user: User = Depends(require_examiner)):
    """Mendapatkan daftar semua profil rubrik."""
    return storage.list_rubrics()


@router.get("/{rubric_id}", response_model=RubricProfile)
def get_rubric(rubric_id: str, current_user: User = Depends(require_examiner)):
    """Mendapatkan detail profil rubrik berdasarkan ID."""
    profile = storage.get_rubric(rubric_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profil rubrik tidak ditemukan")
    return profile


@router.post("", response_model=RubricProfile, status_code=status.HTTP_201_CREATED)
def create_rubric(data: RubricProfileCreate, current_user: User = Depends(require_examiner)):
    """Membuat profil rubrik baru."""
    rubric_id = str(uuid.uuid4())[:8]
    total_w = sum(ind.weight for ind in data.indicators if ind.is_active)
    
    profile = RubricProfile(
        id=rubric_id,
        name=data.name,
        version=data.version,
        description=data.description,
        indicators=data.indicators,
        total_weight=round(total_w, 2),
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat()
    )
    storage.save_rubric(profile)
    return profile


@router.put("/{rubric_id}", response_model=RubricProfile)
def update_rubric(rubric_id: str, data: RubricProfileCreate, current_user: User = Depends(require_examiner)):
    """Memperbarui profil rubrik."""
    existing = storage.get_rubric(rubric_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Profil rubrik tidak ditemukan")
    
    total_w = sum(ind.weight for ind in data.indicators if ind.is_active)
    updated = RubricProfile(
        id=rubric_id,
        name=data.name,
        version=data.version,
        description=data.description,
        indicators=data.indicators,
        total_weight=round(total_w, 2),
        created_at=existing.created_at,
        updated_at=datetime.utcnow().isoformat()
    )
    storage.save_rubric(updated)
    return updated


@router.delete("/{rubric_id}")
def delete_rubric(rubric_id: str, current_user: User = Depends(require_examiner)):
    """Menghapus profil rubrik (kecuali default)."""
    if rubric_id == "default-ukk-mbg-rev1":
        raise HTTPException(status_code=400, detail="Profil rubrik bawaan tidak dapat dihapus")
    
    success = storage.delete_rubric(rubric_id)
    if not success:
        raise HTTPException(status_code=404, detail="Profil rubrik tidak ditemukan")
    return {"message": f"Rubrik {rubric_id} berhasil dihapus"}


@router.post("/{rubric_id}/duplicate", response_model=RubricProfile)
def duplicate_rubric(rubric_id: str, current_user: User = Depends(require_examiner)):
    """Menduplikasi profil rubrik yang ada untuk penyesuaian khusus."""
    existing = storage.get_rubric(rubric_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Profil rubrik asal tidak ditemukan")
    
    new_id = f"custom-{uuid.uuid4().hex[:6]}"
    copied_indicators = [
        RubricIndicator(
            id=f"{ind.id}-copy",
            code=ind.code,
            name=ind.name,
            category=ind.category,
            expected_value=ind.expected_value,
            weight=ind.weight,
            check_method=ind.check_method,
            description=ind.description,
            is_active=ind.is_active
        )
        for ind in existing.indicators
    ]
    
    cloned = RubricProfile(
        id=new_id,
        name=f"{existing.name} (Salinan)",
        version=f"{existing.version}-custom",
        description=f"Salinan dari {existing.name} untuk kebutuhan penyesuaian.",
        indicators=copied_indicators,
        total_weight=existing.total_weight,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat()
    )
    storage.save_rubric(cloned)
    return cloned
