import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class AutorBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre del autor en formato título")
    nacionalidad: Optional[str] = Field(None, max_length=60, description="Nacionalidad del autor")
    anio_nacimiento: Optional[int] = Field(None, description="Año de nacimiento entre 1000 y el año actual")

    @field_validator("nombre")
    @classmethod
    def validar_y_limpiar_nombre(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("El nombre no puede estar vacío")
        limpio = re.sub(r"\s+", " ", v.strip())
        if len(limpio) < 2 or len(limpio) > 100:
            raise ValueError("El nombre debe tener entre 2 y 100 caracteres")
        return limpio.title()

    @field_validator("nacionalidad")
    @classmethod
    def validar_nacionalidad(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = re.sub(r"\s+", " ", v.strip())
            return v if v else None
        return None

    @field_validator("anio_nacimiento")
    @classmethod
    def validar_anio_nacimiento(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            anio_actual = datetime.now().year
            if v < 1000 or v > anio_actual:
                raise ValueError(f"El año de nacimiento debe estar entre 1000 y {anio_actual}")
        return v


class AutorCreate(AutorBase):
    pass


class AutorUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    nacionalidad: Optional[str] = Field(None, max_length=60)
    anio_nacimiento: Optional[int] = None

    @field_validator("nombre")
    @classmethod
    def validar_y_limpiar_nombre(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            limpio = re.sub(r"\s+", " ", v.strip())
            if len(limpio) < 2 or len(limpio) > 100:
                raise ValueError("El nombre debe tener entre 2 y 100 caracteres")
            return limpio.title()
        return None

    @field_validator("nacionalidad")
    @classmethod
    def validar_nacionalidad(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = re.sub(r"\s+", " ", v.strip())
            return v if v else None
        return None

    @field_validator("anio_nacimiento")
    @classmethod
    def validar_anio_nacimiento(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            anio_actual = datetime.now().year
            if v < 1000 or v > anio_actual:
                raise ValueError(f"El año de nacimiento debe estar entre 1000 y {anio_actual}")
        return v


class AutorResponse(BaseModel):
    id: int
    nombre: str
    nacionalidad: Optional[str] = None
    anio_nacimiento: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
