from datetime import datetime
import re
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator

from app.models.usuario import RolUsuario


class UsuarioBase(BaseModel):
    email: EmailStr
    nombre: str = Field(..., min_length=3, max_length=100)

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("El nombre no puede estar vacío")
        limpio = re.sub(r"\s+", " ", v.strip())
        if len(limpio) < 3 or len(limpio) > 100:
            raise ValueError("El nombre debe tener entre 3 y 100 caracteres")
        return limpio.title()

    @field_validator("email")
    @classmethod
    def validar_email(cls, v: str) -> str:
        return v.strip().lower()


class UsuarioRegistro(UsuarioBase):
    telefono: Optional[str] = Field(None, description="Teléfono opcional del socio")
    password: str = Field(..., min_length=8, max_length=64)
    confirmar_password: str = Field(..., min_length=8, max_length=64)

    @field_validator("telefono")
    @classmethod
    def validar_telefono(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            limpio = re.sub(r"\s+", " ", v.strip())
            if not limpio:
                return None
            if not re.match(r"^[\d\s\+]{7,15}$", limpio):
                raise ValueError("El teléfono debe contener entre 7 y 15 caracteres (solo dígitos, espacios o +)")
            return limpio
        return None

    @field_validator("password")
    @classmethod
    def validar_password(cls, v: str) -> str:
        if len(v) < 8 or len(v) > 64:
            raise ValueError("La contraseña debe tener entre 8 y 64 caracteres")
        if not re.search(r"[A-Z]", v):
            raise ValueError("La contraseña debe contener al menos una letra mayúscula")
        if not re.search(r"[a-z]", v):
            raise ValueError("La contraseña debe contener al menos una letra minúscula")
        if not re.search(r"[0-9]", v):
            raise ValueError("La contraseña debe contener al menos un número")
        return v

    @model_validator(mode="after")
    def validar_passwords_coinciden(self) -> "UsuarioRegistro":
        if self.password != self.confirmar_password:
            raise ValueError("Las contraseñas no coinciden")
        return self


class UsuarioCrear(UsuarioBase):
    password: str = Field(..., min_length=8, max_length=64)
    rol: RolUsuario = Field(..., description="Rol: bibliotecario o admin")

    @field_validator("password")
    @classmethod
    def validar_password(cls, v: str) -> str:
        if len(v) < 8 or len(v) > 64:
            raise ValueError("La contraseña debe tener entre 8 y 64 caracteres")
        if not re.search(r"[A-Z]", v):
            raise ValueError("La contraseña debe contener al menos una letra mayúscula")
        if not re.search(r"[a-z]", v):
            raise ValueError("La contraseña debe contener al menos una letra minúscula")
        if not re.search(r"[0-9]", v):
            raise ValueError("La contraseña debe contener al menos un número")
        return v


class UsuarioRespuesta(BaseModel):
    id: int
    email: EmailStr
    nombre: str
    rol: RolUsuario
    activo: bool
    socio_id: Optional[int] = None
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)


class UsuarioRolActualizar(BaseModel):
    rol: RolUsuario


class UsuarioActivoActualizar(BaseModel):
    activo: bool


class SocioActualizarPropio(BaseModel):
    nombre: Optional[str] = Field(None, min_length=3, max_length=100)
    telefono: Optional[str] = None

    model_config = ConfigDict(extra="forbid")

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if not v or not v.strip():
                raise ValueError("El nombre no puede estar vacío")
            limpio = re.sub(r"\s+", " ", v.strip())
            if len(limpio) < 3 or len(limpio) > 100:
                raise ValueError("El nombre debe tener entre 3 y 100 caracteres")
            return limpio.title()
        return None

    @field_validator("telefono")
    @classmethod
    def validar_telefono(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            limpio = re.sub(r"\s+", " ", v.strip())
            if not limpio:
                return None
            if not re.match(r"^[\d\s\+]{7,15}$", limpio):
                raise ValueError("El teléfono debe contener entre 7 y 15 caracteres (solo dígitos, espacios o +)")
            return limpio
        return None
