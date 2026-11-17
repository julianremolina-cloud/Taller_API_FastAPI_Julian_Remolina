from decimal import Decimal
from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from ..core.exceptions import Conflicto, NoEncontrado
from ..models.prestamo import Prestamo
from ..models.socio import Socio
from ..models.usuario import Usuario
from ..schemas.pagina import Pagina
from ..schemas.prestamo import PrestamoResponse
from ..schemas.socio import SocioCreate, SocioResponse, SocioUpdate
from ..schemas.usuario import SocioActualizarPropio


def listar_socios(
    db: Session,
    skip: int,
    limit: int,
    activo: Optional[bool] = None,
) -> Pagina[SocioResponse]:
    """Lista socios con paginación y filtro opcional por estado activo."""
    query = select(Socio)
    if activo is not None:
        query = query.where(Socio.activo.is_(activo))

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.order_by(Socio.id.asc()).offset(skip).limit(limit)).all())

    return Pagina[SocioResponse](
        items=[SocioResponse.model_validate(s) for s in items],
        total=total,
        skip=skip,
        limit=limit,
    )


def obtener_socio_por_id(db: Session, socio_id: int) -> Socio:
    """Obtiene un socio por su ID o lanza 404 si no existe."""
    socio = db.get(Socio, socio_id)
    if not socio:
        raise NoEncontrado(f"Socio con ID {socio_id} no encontrado")
    return socio


def crear_socio(db: Session, socio_in: SocioCreate) -> Socio:
    """Crea un socio verificando que el email sea único."""
    existente = db.scalar(
        select(Socio).where(func.lower(Socio.email) == func.lower(socio_in.email))
    )
    if existente:
        raise Conflicto(f"El email '{socio_in.email}' ya está registrado")

    socio = Socio(
        nombre=socio_in.nombre,
        email=socio_in.email,
        telefono=socio_in.telefono,
        activo=socio_in.activo,
    )
    db.add(socio)
    db.commit()
    db.refresh(socio)
    return socio


def actualizar_socio(
    db: Session,
    socio_id: int,
    socio_in: SocioUpdate,
) -> Socio:
    """Actualiza parcialmente un socio verificando unicidad del email."""
    socio = obtener_socio_por_id(db, socio_id)

    if socio_in.email is not None and socio_in.email != socio.email:
        existente = db.scalar(
            select(Socio).where(
                func.lower(Socio.email) == func.lower(socio_in.email),
                Socio.id != socio_id,
            )
        )
        if existente:
            raise Conflicto(f"El email '{socio_in.email}' ya está registrado por otro socio")
        socio.email = socio_in.email

    if socio_in.nombre is not None:
        socio.nombre = socio_in.nombre
    if socio_in.telefono is not None:
        socio.telefono = socio_in.telefono
    if socio_in.activo is not None:
        socio.activo = socio_in.activo

    db.commit()
    db.refresh(socio)
    return socio


def eliminar_socio(db: Session, socio_id: int) -> None:
    """Elimina un socio si no tiene préstamos activos."""
    socio = obtener_socio_por_id(db, socio_id)

    prestamos_activos = db.scalar(
        select(func.count(Prestamo.id)).where(
            Prestamo.socio_id == socio_id,
            Prestamo.fecha_devolucion.is_(None),
        )
    ) or 0
    if prestamos_activos > 0:
        raise Conflicto(f"No se puede eliminar el socio porque tiene {prestamos_activos} préstamo(s) activo(s)")

    db.delete(socio)
    db.commit()


def obtener_perfil_socio(db: Session, usuario: Usuario) -> Socio:
    """Retorna el registro de Socio vinculado al usuario."""
    if not usuario.socio_id:
        raise NoEncontrado("El usuario no tiene una ficha de socio vinculada")
    return obtener_socio_por_id(db, usuario.socio_id)


def actualizar_perfil_socio(
    db: Session,
    usuario: Usuario,
    datos: SocioActualizarPropio,
) -> Socio:
    """Actualiza únicamente nombre y teléfono del socio autenticado (Z4)."""
    socio = obtener_perfil_socio(db, usuario)

    if datos.nombre is not None:
        socio.nombre = datos.nombre
        usuario.nombre = datos.nombre
    if datos.telefono is not None:
        socio.telefono = datos.telefono

    db.commit()
    db.refresh(socio)
    return socio


def obtener_multas_propias(db: Session, usuario: Usuario) -> dict:
    """Consulta las multas pendientes y calcula el total adeudado."""
    if not usuario.socio_id:
        raise NoEncontrado("El usuario no tiene una ficha de socio vinculada")

    consulta = (
        select(Prestamo)
        .where(
            Prestamo.socio_id == usuario.socio_id,
            Prestamo.multa > 0,
            Prestamo.multa_pagada.is_(False),
        )
        .order_by(Prestamo.id.desc())
    )
    prestamos = list(db.scalars(consulta).all())
    total_adeudado = sum((p.multa for p in prestamos), Decimal("0.00"))

    return {
        "items": [PrestamoResponse.model_validate(p) for p in prestamos],
        "total_adeudado": total_adeudado,
    }
