import re
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class CategoriaBase(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=50, description="Nombre de la categoría en minúsculas")
    descripcion: Optional[str] = Field(None, max_length=200, description="Descripción de la categoría")

    @field_validator("nombre")
    @classmethod
    def validar_y_limpiar_nombre(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("El nombre no puede estar vacío")
        limpio = re.sub(r"\s+", " ", v.strip())
        if len(limpio) < 3 or len(limpio) > 50:
            raise ValueError("El nombre debe tener entre 3 y 50 caracteres")
        return limpio.lower()

    @field_validator("descripcion")
    @classmethod
    def validar_descripcion(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = re.sub(r"\s+", " ", v.strip())
            return v if v else None
        return None


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=3, max_length=50)
    descripcion: Optional[str] = Field(None, max_length=200)

    @field_validator("nombre")
    @classmethod
    def validar_y_limpiar_nombre(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            limpio = re.sub(r"\s+", " ", v.strip())
            if len(limpio) < 3 or len(limpio) > 50:
                raise ValueError("El nombre debe tener entre 3 y 50 caracteres")
            return limpio.lower()
        return None

    @field_validator("descripcion")
    @classmethod
    def validar_descripcion(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v = re.sub(r"\s+", " ", v.strip())
            return v if v else None
        return None


class CategoriaResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
