from typing import Optional
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.core.exceptions import Conflicto, NoEncontrado, ReglaNegocio
from app.core.security import hashear_password
from app.models.refresh_token import RefreshToken
from app.models.usuario import RolUsuario, Usuario
from app.schemas.pagina import Pagina
from app.schemas.usuario import UsuarioCrear, UsuarioRespuesta


def listar_usuarios(
    db: Session,
    skip: int,
    limit: int,
    rol: Optional[RolUsuario] = None,
    activo: Optional[bool] = None,
) -> Pagina[UsuarioRespuesta]:
    """Lista usuarios paginados con filtros opcionales de rol y estado activo."""
    consulta = select(Usuario)
    if rol is not None:
        consulta = consulta.where(Usuario.rol == rol)
    if activo is not None:
        consulta = consulta.where(Usuario.activo.is_(activo))

    total = db.scalar(select(func.count()).select_from(consulta.subquery())) or 0
    items = list(db.scalars(consulta.order_by(Usuario.id.asc()).offset(skip).limit(limit)).all())

    return Pagina[UsuarioRespuesta](
        items=[UsuarioRespuesta.model_validate(u) for u in items],
        total=total,
        skip=skip,
        limit=limit,
    )


def crear_usuario_staff(db: Session, datos: UsuarioCrear) -> Usuario:
    """Crea un nuevo usuario de staff (bibliotecario o admin)."""
    if datos.rol not in (RolUsuario.bibliotecario, RolUsuario.admin):
        raise ReglaNegocio("Solo se pueden crear usuarios con rol bibliotecario o admin")

    email_norm = datos.email.lower()
    existente = db.scalar(select(Usuario).where(Usuario.email == email_norm))
    if existente:
        raise Conflicto("El correo electrónico ya está registrado")

    nuevo_usuario = Usuario(
        email=email_norm,
        nombre=datos.nombre,
        password_hash=hashear_password(datos.password),
        rol=datos.rol,
        activo=True,
        intentos_fallidos=0,
        bloqueado_hasta=None,
        socio_id=None,
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario


def cambiar_rol_usuario(
    db: Session,
    usuario_id: int,
    nuevo_rol: RolUsuario,
    admin_actual: Usuario,
) -> Usuario:
    """
    Cambia el rol de un usuario.
    Regla Z5: Un administrador no puede quitarse el rol a sí mismo (422).
    Regla Z6: Revoca todos los refresh tokens del usuario modificado.
    """
    if usuario_id == admin_actual.id and nuevo_rol != RolUsuario.admin:
        raise ReglaNegocio("Un administrador no puede cambiarse el rol a sí mismo")

    usuario = db.get(Usuario, usuario_id)
    if not usuario:
        raise NoEncontrado(f"Usuario con ID {usuario_id} no encontrado")

    usuario.rol = nuevo_rol

    # Regla Z6: Revocar todos los refresh tokens
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.usuario_id == usuario_id)
        .values(revocado=True)
    )
    db.commit()
    db.refresh(usuario)
    return usuario


def cambiar_activo_usuario(
    db: Session,
    usuario_id: int,
    activo: bool,
    admin_actual: Usuario,
) -> Usuario:
    """
    Activa o desactiva un usuario.
    Regla Z5: Un administrador no puede desactivarse a sí mismo (422).
    Regla Z6: Revoca todos los refresh tokens del usuario modificado.
    """
    if usuario_id == admin_actual.id and not activo:
        raise ReglaNegocio("Un administrador no puede desactivarse a sí mismo")

    usuario = db.get(Usuario, usuario_id)
    if not usuario:
        raise NoEncontrado(f"Usuario con ID {usuario_id} no encontrado")

    usuario.activo = activo

    # Regla Z6: Revocar todos los refresh tokens
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.usuario_id == usuario_id)
        .values(revocado=True)
    )
    db.commit()
    db.refresh(usuario)
    return usuario
