from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from ..core.exceptions import Conflicto, NoEncontrado
from ..models.prestamo import Prestamo
from ..models.socio import Socio
from ..schemas.socio import SocioCreate, SocioUpdate


def listar_socios(
    db: Session,
    skip: int,
    limit: int,
    activo: Optional[bool] = None,
) -> list[Socio]:
    """Lista socios con paginación y filtro opcional por estado activo."""
    query = select(Socio)
    if activo is not None:
        query = query.where(Socio.activo.is_(activo))
    query = query.order_by(Socio.id.asc()).offset(skip).limit(limit)
    return list(db.scalars(query).all())


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


def actualizar_socio(db: Session, socio_id: int, socio_in: SocioUpdate) -> Socio:
    """Actualiza los datos de un socio verificando unicidad de email."""
    socio = obtener_socio_por_id(db, socio_id)
    datos = socio_in.model_dump(exclude_unset=True)

    if "email" in datos and datos["email"]:
        existente = db.scalar(
            select(Socio).where(
                func.lower(Socio.email) == func.lower(datos["email"]),
                Socio.id != socio_id,
            )
        )
        if existente:
            raise Conflicto(f"El email '{datos['email']}' ya está registrado por otro socio")

    for campo, valor in datos.items():
        setattr(socio, campo, valor)

    db.commit()
    db.refresh(socio)
    return socio


def eliminar_socio(db: Session, socio_id: int) -> None:
    """
    Elimina un socio según las reglas:
    - 409 si tiene préstamos sin devolver.
    - Si solo tiene préstamos devueltos, se desactiva (borrado lógico).
    - Si no tiene préstamos, se elimina físicamente.
    """
    socio = obtener_socio_por_id(db, socio_id)

    prestamos_sin_devolver = db.scalar(
        select(func.count(Prestamo.id)).where(
            Prestamo.socio_id == socio_id,
            Prestamo.fecha_devolucion.is_(None),
        )
    ) or 0
    if prestamos_sin_devolver > 0:
        raise Conflicto(
            f"No se puede eliminar el socio porque tiene {prestamos_sin_devolver} préstamos sin devolver"
        )

    total_prestamos = db.scalar(
        select(func.count(Prestamo.id)).where(Prestamo.socio_id == socio_id)
    ) or 0

    if total_prestamos > 0:
        # Borrado lógico: desactivar
        socio.activo = False
        db.commit()
    else:
        # Borrado físico
        db.delete(socio)
        db.commit()


def listar_prestamos_socio(
    db: Session,
    socio_id: int,
    estado: Optional[str] = None,
) -> list[Prestamo]:
    """Lista el historial de préstamos de un socio con filtro opcional por estado."""
    obtener_socio_por_id(db, socio_id)

    consulta = (
        select(Prestamo)
        .options(selectinload(Prestamo.libro), selectinload(Prestamo.socio))
        .where(Prestamo.socio_id == socio_id)
    )

    if estado:
        estado_normalizado = estado.strip().lower()
        if estado_normalizado == "activo":
            consulta = consulta.where(
                Prestamo.fecha_devolucion.is_(None),
                Prestamo.fecha_limite >= func.current_date(),
            )
        elif estado_normalizado == "vencido":
            consulta = consulta.where(
                Prestamo.fecha_devolucion.is_(None),
                Prestamo.fecha_limite < func.current_date(),
            )
        elif estado_normalizado == "devuelto":
            consulta = consulta.where(Prestamo.fecha_devolucion.is_not(None))

    consulta = consulta.order_by(Prestamo.id.desc())
    return list(db.scalars(consulta).all())
