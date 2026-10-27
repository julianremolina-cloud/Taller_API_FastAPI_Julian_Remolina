from typing import Annotated, Generator
from fastapi import Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from .database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    """Generador de sesión de base de datos para inyección de dependencias."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


SessionDep = Annotated[Session, Depends(get_db)]


class Paginacion(BaseModel):
    skip: int = Field(0, ge=0, description="Número de registros a omitir")
    limit: int = Field(10, ge=1, le=100, description="Número máximo de registros a retornar (1-100)")


def paginacion_params(
    skip: int = Query(0, ge=0, description="Número de registros a omitir"),
    limit: int = Query(10, ge=1, le=100, description="Número máximo de registros a retornar (1-100)"),
) -> Paginacion:
    """Dependencia reutilizable para paginación con validación de límites."""
    return Paginacion(skip=skip, limit=limit)


PaginacionDep = Annotated[Paginacion, Depends(paginacion_params)]
