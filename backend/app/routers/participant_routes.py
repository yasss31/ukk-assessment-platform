"""
app/routers/participant_routes.py - API Manajemen Peserta UKK
"""
import uuid
from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from app.models.schemas import Participant, ParticipantCreate, User
from app.auth import get_current_user, require_examiner
from app.database.storage import storage

router = APIRouter(prefix="/api/participants", tags=["Peserta UKK"])


@router.get("", response_model=List[Participant])
def list_participants(current_user: User = Depends(require_examiner)):
    """Mendapatkan daftar seluruh peserta UKK."""
    return storage.list_participants()


@router.get("/{participant_id}", response_model=Participant)
def get_participant(participant_id: str, current_user: User = Depends(require_examiner)):
    """Mendapatkan detail peserta berdasarkan ID."""
    p = storage.get_participant(participant_id)
    if not p:
        raise HTTPException(status_code=404, detail="Peserta tidak ditemukan")
    return p


@router.post("", response_model=Participant, status_code=status.HTTP_201_CREATED)
def create_participant(data: ParticipantCreate, current_user: User = Depends(require_examiner)):
    """Mendaftarkan peserta UKK baru."""
    # Periksa nomor peserta duplikat
    existing = storage.list_participants()
    for p in existing:
        if p.participant_number.strip().lower() == data.participant_number.strip().lower():
            raise HTTPException(status_code=400, detail=f"Nomor peserta '{data.participant_number}' sudah terdaftar")

    new_p = Participant(
        id=f"part-{uuid.uuid4().hex[:6]}",
        name=data.name.strip(),
        participant_number=data.participant_number.strip(),
        student_class=data.student_class.strip(),
        school=data.school.strip(),
        created_at=datetime.utcnow().isoformat()
    )
    storage.save_participant(new_p)
    return new_p


@router.delete("/{participant_id}")
def delete_participant(participant_id: str, current_user: User = Depends(require_examiner)):
    """Menghapus data peserta."""
    success = storage.delete_participant(participant_id)
    if not success:
        raise HTTPException(status_code=404, detail="Peserta tidak ditemukan")
    return {"message": "Peserta berhasil dihapus"}

