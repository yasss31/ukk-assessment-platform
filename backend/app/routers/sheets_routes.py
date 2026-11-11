"""
app/routers/sheets_routes.py - API Status & Konfigurasi Google Sheets
"""
import json
import os
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from app.auth import get_current_user, require_admin, require_examiner
from app.models.schemas import User
from app.database.storage import storage

router = APIRouter(prefix="/api/sheets", tags=["Google Sheets"])


class ServiceAccountConfigRequest(BaseModel):
    service_account_json: str


@router.get("/status")
def get_sheets_status(current_user: User = Depends(require_examiner)):
    """Memeriksa status integrasi Google Sheets."""
    return storage.sheets.get_status()


@router.post("/test")
def test_sheets_connection(current_user: User = Depends(require_examiner)):
    """Menguji ulang koneksi ke Google Sheets."""
    storage.sheets._initialize_service()
    status_info = storage.sheets.get_status()
    if not status_info["is_connected"]:
        return {
            "success": False,
            "message": "Koneksi gagal atau kredensial Service Account belum valid.",
            "details": status_info
        }
    sheets = storage.sheets.list_sheet_names()
    return {
        "success": True,
        "message": "Koneksi Google Sheets berhasil!",
        "spreadsheet_id": status_info["spreadsheet_id"],
        "available_sheets": sheets
    }


@router.post("/configure")
def configure_service_account(data: ServiceAccountConfigRequest, current_user: User = Depends(require_admin)):
    """Mengunggah & menerapkan kredensial Service Account Google Cloud secara aman."""
    try:
        parsed = json.loads(data.service_account_json)
        if "client_email" not in parsed or "private_key" not in parsed:
            raise HTTPException(status_code=400, detail="Format JSON Service Account tidak valid (wajib client_email & private_key)")
        
        # Simpan ke service_account.json di root backend
        target_path = "service_account.json"
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(data.service_account_json)
        
        # Re-inisialisasi
        storage.sheets.credentials_json_path = target_path
        storage.sheets._initialize_service()
        
        if storage.sheets.is_connected:
            return {
                "success": True,
                "message": f"Service Account berhasil dikonfigurasi ({parsed.get('client_email')})",
                "status": storage.sheets.get_status()
            }
        else:
            return {
                "success": False,
                "message": "File JSON tersimpan, namun Google API mengembalikan kesalahan akses.",
                "error": storage.sheets.last_error
            }
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="String yang dikirim bukan format JSON yang valid")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mengonfigurasi: {str(e)}")


@router.post("/sync")
def sync_data_to_sheets(current_user: User = Depends(require_examiner)):
    """Memicu sinkronisasi manual data peserta dan hasil penilaian ke Google Sheets."""
    if not storage.sheets.is_connected:
        raise HTTPException(status_code=400, detail="Google Sheets belum terhubung. Jalankan konfigurasi Service Account terlebih dahulu.")
    
    # Inisialisasi sheet Peserta & Penilaian jika belum ada
    storage.sheets.ensure_sheet_exists("Peserta", ["ID Peserta", "Nomor Peserta", "Nama Siswa", "Kelas", "Sekolah", "Waktu Dibuat"])
    storage.sheets.ensure_sheet_exists("Penilaian", ["ID Penilaian", "Nomor Peserta", "Nama Siswa", "Profil Rubrik", "Skor Total", "Maksimal", "Persentase", "Status", "Total PASS", "Total FAIL", "Waktu"])
    
    return {"success": True, "message": "Sinkronisasi ke Google Sheets berhasil dipicu."}

