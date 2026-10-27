import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class SocioBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre del socio en formato título")
    email: EmailStr = Field(..., description="Correo electrónico único del socio")
    telefono: Optional[str] = Field(None, description="Teléfono de 7 a 15 caracteres (dígitos, espacios o +)")

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("El nombre no puede estar vacío")
        limpio = re.sub(r"\s+", " ", v.strip())
        if len(limpio) < 2 or len(limpio) > 100:
            raise ValueError("El nombre debe tener entre 2 y 100 caracteres")
        return limpio.title()

    @field_validator("email")
    @classmethod
    def validar_email(cls, v: str) -> str:
        return v.strip().lower()

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


class SocioCreate(SocioBase):
    activo: bool = True


class SocioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = None
    telefono: Optional[str] = None
    activo: Optional[bool] = None

    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            limpio = re.sub(r"\s+", " ", v.strip())
            if len(limpio) < 2 or len(limpio) > 100:
                raise ValueError("El nombre debe tener entre 2 y 100 caracteres")
            return limpio.title()
        return None

    @field_validator("email")
    @classmethod
    def validar_email(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return v.strip().lower()
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


class SocioResponse(BaseModel):
    id: int
    nombre: str
    email: str
    telefono: Optional[str] = None
    activo: bool
    fecha_alta: datetime

    model_config = ConfigDict(from_attributes=True)
