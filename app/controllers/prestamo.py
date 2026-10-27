from datetime import date, timedelta
from decimal import Decimal
from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from ..core.exceptions import Conflicto, NoEncontrado, ReglaNegocio
from ..models.libro import Libro
from ..models.prestamo import Prestamo
from ..models.socio import Socio
from ..schemas.prestamo import DevolucionCreate, PrestamoCreate
from .libro import _calcular_disponibles_uno


def listar_prestamos(
    db: Session,
    skip: int,
    limit: int,
    estado: Optional[str] = None,
    socio_id: Optional[int] = None,
    libro_id: Optional[int] = None,
) -> list[Prestamo]:
    """Lista préstamos con filtros combinables y paginación."""
    hoy = date.today()
    consulta = select(Prestamo)

    if socio_id is not None:
        consulta = consulta.where(Prestamo.socio_id == socio_id)
    if libro_id is not None:
        consulta = consulta.where(Prestamo.libro_id == libro_id)

    if estado:
        estado_normalizado = estado.strip().lower()
        if estado_normalizado == "activo":
            consulta = consulta.where(
                Prestamo.fecha_devolucion.is_(None),
                Prestamo.fecha_limite >= hoy,
            )
        elif estado_normalizado == "vencido":
            consulta = consulta.where(
                Prestamo.fecha_devolucion.is_(None),
                Prestamo.fecha_limite < hoy,
            )
        elif estado_normalizado == "devuelto":
            consulta = consulta.where(Prestamo.fecha_devolucion.is_not(None))

    consulta = consulta.order_by(Prestamo.id.desc()).offset(skip).limit(limit)
    return list(db.scalars(consulta).all())


def obtener_prestamo_por_id(db: Session, prestamo_id: int) -> Prestamo:
    """Obtiene un préstamo por su ID con libro y socio anidados."""
    consulta = (
        select(Prestamo)
        .options(
            selectinload(Prestamo.libro).options(
                selectinload(Libro.autor),
                selectinload(Libro.categorias),
            ),
            selectinload(Prestamo.socio),
        )
        .where(Prestamo.id == prestamo_id)
    )
    prestamo = db.scalar(consulta)
    if not prestamo:
        raise NoEncontrado(f"Préstamo con ID {prestamo_id} no encontrado")

    if prestamo.libro:
        _calcular_disponibles_uno(db, prestamo.libro)

    return prestamo


def registrar_prestamo(db: Session, prestamo_in: PrestamoCreate) -> Prestamo:
    """
    Registra un préstamo aplicando estrictamente las reglas R1 a R8 en orden:
    R1: El socio existe (404)
    R2: El libro existe (404)
    R3: El socio está activo (422)
    R4: El socio no tiene préstamos vencidos (422)
    R5: El socio tiene menos de 3 préstamos sin devolver (422)
    R6: El socio no tiene ya ese mismo libro sin devolver (409)
    R7: El libro tiene ejemplares disponibles (422)
    R8: fecha_limite = fecha_prestamo + dias
    """
    hoy = date.today()

    # R1: El socio existe
    socio = db.get(Socio, prestamo_in.socio_id)
    if not socio:
        raise NoEncontrado(f"Socio con ID {prestamo_in.socio_id} no encontrado")

    # R2: El libro existe
    libro = db.get(Libro, prestamo_in.libro_id)
    if not libro:
        raise NoEncontrado(f"Libro con ID {prestamo_in.libro_id} no encontrado")

    # R3: El socio está activo
    if not socio.activo:
        raise ReglaNegocio("El socio no está activo")

    # R4: El socio no tiene préstamos vencidos
    prestamos_vencidos = db.scalar(
        select(func.count(Prestamo.id)).where(
            Prestamo.socio_id == socio.id,
            Prestamo.fecha_devolucion.is_(None),
            Prestamo.fecha_limite < hoy,
        )
    ) or 0
    if prestamos_vencidos > 0:
        raise ReglaNegocio("El socio tiene préstamos vencidos")

    # R5: El socio tiene menos de 3 préstamos sin devolver
    prestamos_sin_devolver = db.scalar(
        select(func.count(Prestamo.id)).where(
            Prestamo.socio_id == socio.id,
            Prestamo.fecha_devolucion.is_(None),
        )
    ) or 0
    if prestamos_sin_devolver >= 3:
        raise ReglaNegocio("Máximo de 3 préstamos")

    # R6: El socio no tiene ya ese mismo libro sin devolver
    mismo_libro_activo = db.scalar(
        select(func.count(Prestamo.id)).where(
            Prestamo.socio_id == socio.id,
            Prestamo.libro_id == libro.id,
            Prestamo.fecha_devolucion.is_(None),
        )
    ) or 0
    if mismo_libro_activo > 0:
        raise Conflicto("El socio ya tiene este libro en préstamo")

    # R7: El libro tiene ejemplares disponibles
    prestamos_libro_activos = db.scalar(
        select(func.count(Prestamo.id)).where(
            Prestamo.libro_id == libro.id,
            Prestamo.fecha_devolucion.is_(None),
        )
    ) or 0
    disponibles = libro.ejemplares - prestamos_libro_activos
    if disponibles <= 0:
        raise ReglaNegocio("No hay ejemplares disponibles")

    # R8: fecha_limite = fecha_prestamo + dias
    fecha_p = prestamo_in.fecha_prestamo or hoy
    fecha_l = fecha_p + timedelta(days=prestamo_in.dias)

    nuevo_prestamo = Prestamo(
        libro_id=libro.id,
        socio_id=socio.id,
        fecha_prestamo=fecha_p,
        fecha_limite=fecha_l,
        fecha_devolucion=None,
        multa=Decimal("0.00"),
    )
    db.add(nuevo_prestamo)
    db.commit()
    db.refresh(nuevo_prestamo)
    return nuevo_prestamo


def registrar_devolucion(
    db: Session,
    prestamo_id: int,
    devolucion_in: DevolucionCreate,
) -> Prestamo:
    """
    Registra la devolución aplicando las reglas R9 y R10:
    R9:
      - El préstamo existe (404)
      - No fue devuelto antes (409)
      - La fecha de devolución no es anterior a la del préstamo (422)
    R10:
      - Si se devuelve tarde: multa = días de retraso * 0.50
    """
    hoy = date.today()
    fecha_dev = devolucion_in.fecha_devolucion or hoy

    # R9: Préstamo existe
    prestamo = db.get(Prestamo, prestamo_id)
    if not prestamo:
        raise NoEncontrado(f"Préstamo con ID {prestamo_id} no encontrado")

    # R9: No devuelto antes
    if prestamo.fecha_devolucion is not None:
        raise Conflicto("El préstamo ya fue devuelto")

    # R9: Fecha no anterior a la de préstamo
    if fecha_dev < prestamo.fecha_prestamo:
        raise ReglaNegocio("La fecha de devolución no puede ser anterior a la fecha de préstamo")

    # R10: Cálculo de multa si hay retraso
    multa = Decimal("0.00")
    if fecha_dev > prestamo.fecha_limite:
        dias_retraso = (fecha_dev - prestamo.fecha_limite).days
        multa = Decimal(str(round(dias_retraso * 0.50, 2)))

    prestamo.fecha_devolucion = fecha_dev
    prestamo.multa = multa
    db.commit()
    db.refresh(prestamo)
    return prestamo
