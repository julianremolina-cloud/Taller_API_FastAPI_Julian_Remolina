import re
from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from .autor import AutorResponse
from .categoria import CategoriaResponse


class OrdenLibrosEnum(str, Enum):
    titulo = "titulo"
    anio = "anio"
    menos_anio = "-anio"


class LibroBase(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=150, description="Título del libro en formato título")
    isbn: str = Field(..., pattern=r"^\d{13}$", description="Código ISBN de exactamente 13 dígitos")
    anio_publicacion: int = Field(..., ge=1450, description="Año de publicación entre 1450 y el año actual")
    ejemplares: int = Field(..., ge=1, le=50, description="Número de ejemplares (entre 1 y 50)")
    autor_id: int = Field(..., description="ID del autor del libro")

    @field_validator("titulo")
    @classmethod
    def validar_titulo(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("El título no puede estar vacío")
        limpio = re.sub(r"\s+", " ", v.strip())
        if len(limpio) < 1 or len(limpio) > 150:
            raise ValueError("El título debe tener entre 1 y 150 caracteres")
        return limpio.title()

    @field_validator("anio_publicacion")
    @classmethod
    def validar_anio(cls, v: int) -> int:
        anio_actual = datetime.now().year
        if v < 1450 or v > anio_actual:
            raise ValueError(f"El año de publicación debe estar entre 1450 y {anio_actual}")
        return v


class LibroCreate(LibroBase):
    categoria_ids: list[int] = Field(..., description="Lista de IDs de categorías (entre 1 y 5, sin repetidos)")

    @field_validator("categoria_ids")
    @classmethod
    def validar_categoria_ids(cls, v: list[int]) -> list[int]:
        if not v or len(v) < 1 or len(v) > 5:
            raise ValueError("Debe asignar entre 1 y 5 categorías")
        if len(v) != len(set(v)):
            raise ValueError("No se permiten categorías repetidas")
        return v


class LibroUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=1, max_length=150)
    isbn: Optional[str] = Field(None, pattern=r"^\d{13}$")
    anio_publicacion: Optional[int] = Field(None, ge=1450)
    ejemplares: Optional[int] = Field(None, ge=1, le=50)
    autor_id: Optional[int] = None
    categoria_ids: Optional[list[int]] = None

    @field_validator("titulo")
    @classmethod
    def validar_titulo(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            limpio = re.sub(r"\s+", " ", v.strip())
            if len(limpio) < 1 or len(limpio) > 150:
                raise ValueError("El título debe tener entre 1 y 150 caracteres")
            return limpio.title()
        return None

    @field_validator("anio_publicacion")
    @classmethod
    def validar_anio(cls, v: Optional[int]) -> Optional[int]:
        if v is not None:
            anio_actual = datetime.now().year
            if v < 1450 or v > anio_actual:
                raise ValueError(f"El año de publicación debe estar entre 1450 y {anio_actual}")
        return v

    @field_validator("categoria_ids")
    @classmethod
    def validar_categoria_ids(cls, v: Optional[list[int]]) -> Optional[list[int]]:
        if v is not None:
            if len(v) < 1 or len(v) > 5:
                raise ValueError("Debe asignar entre 1 y 5 categorías")
            if len(v) != len(set(v)):
                raise ValueError("No se permiten categorías repetidas")
        return v


class LibroResponse(BaseModel):
    id: int
    titulo: str
    isbn: str
    anio_publicacion: int
    ejemplares: int
    disponibles: int
    autor: AutorResponse
    categorias: list[CategoriaResponse]

    model_config = ConfigDict(from_attributes=True)
