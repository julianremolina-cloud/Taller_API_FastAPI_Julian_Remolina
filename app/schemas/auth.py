import re
from pydantic import BaseModel, Field, field_validator


class TokenRespuesta(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenSolicitud(BaseModel):
    refresh_token: str


class PasswordCambiar(BaseModel):
    password_actual: str
    password_nueva: str = Field(..., min_length=8, max_length=64)

    @field_validator("password_nueva")
    @classmethod
    def validar_password_nueva(cls, v: str) -> str:
        if len(v) < 8 or len(v) > 64:
            raise ValueError("La contraseña debe tener entre 8 y 64 caracteres")
        if not re.search(r"[A-Z]", v):
            raise ValueError("La contraseña debe contener al menos una letra mayúscula")
        if not re.search(r"[a-z]", v):
            raise ValueError("La contraseña debe contener al menos una letra minúscula")
        if not re.search(r"[0-9]", v):
            raise ValueError("La contraseña debe contener al menos un número")
        return v
