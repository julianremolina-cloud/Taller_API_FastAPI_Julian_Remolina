from typing import Annotated, Generator
import jwt
from fastapi import Depends, Query
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.exceptions import NoAutenticado, Prohibido
from app.models.usuario import RolUsuario, Usuario

settings = get_settings()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_db() -> Generator[Session, None, None]:
    """Generador de sesión de base de datos para inyección de dependencias."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


SessionDep = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: SessionDep,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> Usuario:
    """Verifica el token JWT y recupera el usuario actual de la base de datos."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except jwt.InvalidTokenError:
        raise NoAutenticado("Token inválido o vencido")

    if payload.get("type") != "access":
        raise NoAutenticado("Tipo de token inválido")

    sub = payload.get("sub")
    if not sub:
        raise NoAutenticado("Token sin identificador de usuario")

    try:
        usuario_id = int(sub)
    except ValueError:
        raise NoAutenticado("Identificador de usuario inválido")

    usuario = db.get(Usuario, usuario_id)
    if not usuario:
        raise NoAutenticado("Usuario no encontrado")

    if not usuario.activo:
        raise Prohibido("Usuario inactivo")

    return usuario


CurrentUser = Annotated[Usuario, Depends(get_current_user)]


def requiere_rol(*roles: RolUsuario):
    """Dependencia que valida que el usuario posea uno de los roles autorizados."""
    def verificar(usuario: CurrentUser) -> Usuario:
        if usuario.rol not in roles:
            raise Prohibido("No tiene permisos para esta acción")
        return usuario

    return Depends(verificar)


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
