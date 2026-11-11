"""
app/routers/auth_routes.py - Endpoint Autentikasi Pengguna & Sesi
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.auth import _USERS_STORE, verify_password, hash_password, create_access_token, get_current_user
from app.models.schemas import User, Token, PasswordChangeRequest

router = APIRouter(prefix="/api/auth", tags=["Authentication"])



@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    username = form_data.username.strip()
    if username not in _USERS_STORE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_dict = _USERS_STORE[username]
    if not verify_password(form_data.password, user_dict["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user_dict.get("is_active", True):
        raise HTTPException(status_code=400, detail="Akun dinonaktifkan")

    user_obj = User(
        id=user_dict["id"],
        username=user_dict["username"],
        full_name=user_dict["full_name"],
        role=user_dict["role"],
        email=user_dict.get("email"),
        is_active=user_dict.get("is_active", True),
        created_at=user_dict.get("created_at")
    )
    token = create_access_token({"sub": user_obj.username, "role": user_obj.role.value})
    return Token(access_token=token, token_type="bearer", user=user_obj)


@router.get("/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/change-password")
async def change_password(data: PasswordChangeRequest, current_user: User = Depends(get_current_user)):
    """Memperbarui kata sandi akun secara aman dengan HMAC-SHA256 ber-salt."""
    user_dict = _USERS_STORE.get(current_user.username)
    if not user_dict:
        raise HTTPException(status_code=404, detail="Akun pengguna tidak ditemukan")
    if not verify_password(data.current_password, user_dict["password_hash"]):
        raise HTTPException(status_code=400, detail="Kata sandi lama yang Anda masukkan salah")
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Kata sandi baru minimal 6 karakter")
    
    user_dict["password_hash"] = hash_password(data.new_password)
    user_dict["must_change_password"] = False
    return {"message": "Kata sandi berhasil diperbarui"}


