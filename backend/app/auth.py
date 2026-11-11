"""
app/auth.py - Modul Autentikasi dan Otorisasi (JWT & Hashing)
"""
import os
import time
import json
import base64
import hmac
import hashlib
from typing import Optional, Dict
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES, SUPER_ADMIN_USERNAME, SUPER_ADMIN_PASSWORD, SUPER_ADMIN_NAME
from app.models.schemas import User, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# In-memory users store (diinisialisasi dengan Super Admin)
_USERS_STORE: Dict[str, Dict] = {}


def hash_password(password: str) -> str:
    """Hash password dengan HMAC-SHA256 ber-salt untuk keandalan murni tanpa C-dependency."""
    salt = "ukk_secure_salt_2026"
    return hmac.new((SECRET_KEY + salt).encode(), password.encode(), hashlib.sha256).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return hmac.compare_digest(hash_password(plain_password), hashed_password)


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Memvalidasi username dan password, mengembalikan user dict jika valid."""
    u = _USERS_STORE.get(username.strip())
    if not u:
        return None
    if not verify_password(password, u["password_hash"]):
        return None
    return u



def init_default_users():
    """Inisialisasi akun Super Admin default."""
    if SUPER_ADMIN_USERNAME not in _USERS_STORE:
        _USERS_STORE[SUPER_ADMIN_USERNAME] = {
            "id": "usr-admin-01",
            "username": SUPER_ADMIN_USERNAME,
            "password_hash": hash_password(SUPER_ADMIN_PASSWORD),
            "full_name": SUPER_ADMIN_NAME,
            "role": UserRole.SUPER_ADMIN,
            "email": "admin@smkn1bms.sch.id",
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        }
    # Tambah contoh akun Examiner
    if "penguji1" not in _USERS_STORE:
        _USERS_STORE["penguji1"] = {
            "id": "usr-examiner-01",
            "username": "penguji1",
            "password_hash": hash_password("penguji123"),
            "full_name": "Penguji UKK Cloud 1",
            "role": UserRole.EXAMINER,
            "email": "penguji1@smkn1bms.sch.id",
            "is_active": True,
            "created_at": datetime.utcnow().isoformat()
        }


init_default_users()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Membuat JWT token yang ditandatangani HMAC-SHA256 secara portabel."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": int(expire.timestamp())})
    
    header = {"alg": "HS256", "typ": "JWT"}
    header_b64 = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
    payload_b64 = base64.urlsafe_b64encode(json.dumps(to_encode).encode()).decode().rstrip("=")
    signature = hmac.new(
        SECRET_KEY.encode(),
        f"{header_b64}.{payload_b64}".encode(),
        hashlib.sha256
    ).digest()
    sig_b64 = base64.urlsafe_b64encode(signature).decode().rstrip("=")
    return f"{header_b64}.{payload_b64}.{sig_b64}"


def decode_access_token(token: str) -> Optional[dict]:
    """Decode dan verifikasi JWT token."""
    try:
        parts = token.split(".")
        if len(parts) != 3:
            return None
        header_b64, payload_b64, sig_b64 = parts
        
        # Verifikasi tanda tangan
        expected_sig = hmac.new(
            SECRET_KEY.encode(),
            f"{header_b64}.{payload_b64}".encode(),
            hashlib.sha256
        ).digest()
        
        # Tambahkan padding jika diperlukan
        pad = len(sig_b64) % 4
        sig_bytes = base64.urlsafe_b64decode(sig_b64 + ("=" * (4 - pad) if pad else ""))
        if not hmac.compare_digest(expected_sig, sig_bytes):
            return None
            
        pad_p = len(payload_b64) % 4
        payload_bytes = base64.urlsafe_b64decode(payload_b64 + ("=" * (4 - pad_p) if pad_p else ""))
        payload = json.loads(payload_bytes.decode())
        
        # Periksa waktu kedaluwarsa
        if payload.get("exp") and payload["exp"] < int(time.time()):
            return None
        return payload
    except Exception:
        return None


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Sesi tidak valid atau telah kedaluwarsa",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_access_token(token)
    if not payload:
        raise credentials_exception
    username: str = payload.get("sub")
    if not username or username not in _USERS_STORE:
        raise credentials_exception
    user_data = _USERS_STORE[username]
    if not user_data.get("is_active"):
        raise HTTPException(status_code=400, detail="Akun dinonaktifkan")
    return User(
        id=user_data["id"],
        username=user_data["username"],
        full_name=user_data["full_name"],
        role=user_data["role"],
        email=user_data.get("email"),
        is_active=user_data.get("is_active", True),
        created_at=user_data.get("created_at")
    )


async def require_super_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.SUPER_ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Akses ditolak: Operasi ini membutuhkan hak akses Super Admin"
        )
    return current_user


require_admin = require_super_admin
require_examiner = get_current_user

