"""
app/routers/auth_routes.py - Endpoint Autentikasi Pengguna & Sesi
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from app.auth import _USERS_STORE, verify_password, create_access_token, get_current_user
from app.models.schemas import User, Token

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
