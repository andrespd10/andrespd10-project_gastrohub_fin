from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
import random

from app.db.session import get_db
from app.services.usuario import UsuarioService
from app.schemas.schemas import (
    LoginRequest,
    Token,
    PasswordResetRequest,
    PasswordResetConfirm,
)
from app.core.security import (
    verify_password,
    create_token,
    decode_token,
    TokenType,
)
# ⚠️ NO importar get_password_hash aquí (lo hace el service)

router = APIRouter(prefix="/auth", tags=["Auth"])

# Almacenamiento temporal de OTP (solo simulación)
_otp_storage: dict[str, tuple[str, datetime]] = {}


# ------------------------
# UTILIDADES OTP
# ------------------------

def _generate_otp() -> str:
    """Genera un código OTP de 6 dígitos."""
    return f"{random.randint(100000, 999999)}"


def _verify_otp(email: str, code: str) -> bool:
    """Valida el OTP almacenado."""
    if email not in _otp_storage:
        return False

    saved_code, expires_at = _otp_storage[email]

    if datetime.now(timezone.utc) > expires_at:
        del _otp_storage[email]
        return False

    if saved_code != code:
        return False

    del _otp_storage[email]
    return True


# ------------------------
# LOGIN
# ------------------------

@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Autenticación de usuario.

    Valida credenciales y retorna un JWT.
    """

    user = UsuarioService().get_by_email(db, payload.email)

    if not user or not user.activo or not verify_password(payload.password, user.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales inválidas"
        )

    token = create_token(
        subject=user.email,
        token_type=TokenType.ACCESS
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


# ------------------------
# RECUPERACIÓN DE CONTRASEÑA
# ------------------------

@router.post("/request-password-reset")
def request_password_reset(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    """
    Solicita recuperación de contraseña.

    Genera token tipo RESET (15 minutos).
    """

    user = UsuarioService().get_by_email(db, payload.email)

    token = create_token(
        subject=payload.email,
        token_type=TokenType.RESET,
        expires_delta=timedelta(minutes=15)
    )

    # Simulación de envío de correo
    if user and user.activo:
        print(f"[RECUPERACIÓN] {payload.email} -> token: {token}")

    return {
        "message": "Si el email existe, se ha enviado un link de recuperación"
    }


@router.post("/reset-password")
def reset_password(payload: PasswordResetConfirm, db: Session = Depends(get_db)):
    """
    Restablece la contraseña usando token RESET.
    """

    decoded = decode_token(payload.token, token_type=TokenType.RESET)

    if not decoded:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido o expirado"
        )

    email = decoded.get("sub")

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido"
        )

    user = UsuarioService().get_by_email(db, email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Token inválido"
        )

    # ⚠️ El service ya hace el hash
    UsuarioService().update(db, user.id, {
        "password": payload.new_password
    })

    return {
        "message": "Contraseña actualizada correctamente"
    }


# ------------------------
# OTP (SIMULADO)
# ------------------------

@router.post("/request-otp")
def request_otp(payload: PasswordResetRequest, db: Session = Depends(get_db)):
    """
    Genera y envía OTP (simulado).
    """

    user = UsuarioService().get_by_email(db, payload.email)

    if user and user.activo:
        code = _generate_otp()
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

        _otp_storage[payload.email] = (code, expires_at)

        print(f"[OTP] {payload.email} -> {code}")

    return {
        "message": "Si el email existe, se ha enviado un código OTP"
    }


@router.post("/verify-otp", response_model=Token)
def verify_otp(payload: LoginRequest, db: Session = Depends(get_db)):
    """
    Verifica OTP y genera JWT.
    """

    if not _verify_otp(payload.email, payload.password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP inválido"
        )

    user = UsuarioService().get_by_email(db, payload.email)

    if not user or not user.activo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario no activo"
        )

    token = create_token(
        subject=user.email,
        token_type=TokenType.ACCESS
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }