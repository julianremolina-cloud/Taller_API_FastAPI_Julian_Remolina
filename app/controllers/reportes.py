from decimal import Decimal
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from ..models.autor import Autor
from ..models.categoria import Categoria
from ..models.libro import Libro, libro_categoria
from ..models.prestamo import Prestamo
from ..models.socio import Socio
from ..schemas.reportes import (
    AutorReporte,
    CategoriaReporte,
    LibroMasPrestadoReporte,
    PrestamoVencidoReporte,
    ResumenReporte,
    SocioConMultasReporte,
)


def reporte_libros_mas_prestados(db: Session, limite: int = 5) -> list[LibroMasPrestadoReporte]:
    """Libro, autor y total de préstamos, de mayor a menor con join + group_by + count + order_by."""
    stmt = (
        select(
            Libro.id.label("libro_id"),
            Libro.titulo,
            Autor.nombre.label("autor"),
            func.count(Prestamo.id).label("total_prestamos"),
        )
        .join(Libro.autor)
        .join(Prestamo, Prestamo.libro_id == Libro.id)
        .group_by(Libro.id, Libro.titulo, Autor.nombre)
        .order_by(func.count(Prestamo.id).desc())
        .limit(limite)
    )
    filas = db.execute(stmt).mappings().all()
    return [LibroMasPrestadoReporte.model_validate(dict(f)) for f in filas]


def reporte_categorias(db: Session) -> list[CategoriaReporte]:
    """Total de libros por categoría, incluidas las que tienen 0 con outerjoin + group_by."""
    total = func.count(libro_categoria.c.libro_id).label("total_libros")
    stmt = (
        select(
            Categoria.id,
            Categoria.nombre,
            total,
        )
        .outerjoin(libro_categoria, libro_categoria.c.categoria_id == Categoria.id)
        .group_by(Categoria.id, Categoria.nombre)
        .order_by(Categoria.id.asc())
    )
    filas = db.execute(stmt).mappings().all()
    return [CategoriaReporte.model_validate(dict(f)) for f in filas]


def reporte_prestamos_vencidos(db: Session) -> list[PrestamoVencidoReporte]:
    """Préstamo, título, socio, email, fecha límite y días de retraso con join de 3 tablas + where."""
    dias = (func.current_date() - Prestamo.fecha_limite).label("dias_retraso")
    stmt = (
        select(
            Prestamo.id.label("prestamo_id"),
            Libro.titulo,
            Socio.nombre.label("socio"),
            Socio.email,
            Prestamo.fecha_limite,
            dias,
        )
        .join(Libro, Prestamo.libro_id == Libro.id)
        .join(Socio, Prestamo.socio_id == Socio.id)
        .where(
            Prestamo.fecha_devolucion.is_(None),
            Prestamo.fecha_limite < func.current_date(),
        )
        .order_by(dias.desc())
    )
    filas = db.execute(stmt).mappings().all()
    return [PrestamoVencidoReporte.model_validate(dict(f)) for f in filas]


def reporte_socios_con_multas(db: Session) -> list[SocioConMultasReporte]:
    """Socio, total de multas y préstamos con multa con group_by + sum + having."""
    stmt = (
        select(
            Socio.id.label("socio_id"),
            Socio.nombre,
            Socio.email,
            func.sum(Prestamo.multa).label("total_multas"),
            func.count(Prestamo.id).label("prestamos_con_multa"),
        )
        .join(Prestamo, Prestamo.socio_id == Socio.id)
        .where(Prestamo.multa > 0)
        .group_by(Socio.id, Socio.nombre, Socio.email)
        .having(func.sum(Prestamo.multa) > 0)
        .order_by(func.sum(Prestamo.multa).desc())
    )
    filas = db.execute(stmt).mappings().all()
    return [SocioConMultasReporte.model_validate(dict(f)) for f in filas]


def reporte_autores(db: Session) -> list[AutorReporte]:
    """Libros, ejemplares y préstamos de cada autor resuelto en una sola consulta SQL."""
    libros_cte = (
        select(
            Libro.autor_id,
            func.count(Libro.id).label("total_libros"),
            func.sum(Libro.ejemplares).label("total_ejemplares"),
        )
        .group_by(Libro.autor_id)
        .cte("libros_cte")
    )
    prestamos_cte = (
        select(
            Libro.autor_id,
            func.count(Prestamo.id).label("total_prestamos"),
        )
        .join(Prestamo, Prestamo.libro_id == Libro.id)
        .group_by(Libro.autor_id)
        .cte("prestamos_cte")
    )
    stmt = (
        select(
            Autor.id.label("autor_id"),
            Autor.nombre,
            func.coalesce(libros_cte.c.total_libros, 0).label("total_libros"),
            func.coalesce(libros_cte.c.total_ejemplares, 0).label("total_ejemplares"),
            func.coalesce(prestamos_cte.c.total_prestamos, 0).label("total_prestamos"),
        )
        .outerjoin(libros_cte, libros_cte.c.autor_id == Autor.id)
        .outerjoin(prestamos_cte, prestamos_cte.c.autor_id == Autor.id)
        .order_by(Autor.id.asc())
    )
    filas = db.execute(stmt).mappings().all()
    return [AutorReporte.model_validate(dict(f)) for f in filas]


def reporte_resumen(db: Session) -> ResumenReporte:
    """Totales del sistema en una sola consulta SQL con select(func.count()) y func.sum."""
    stmt = select(
        select(func.count(Libro.id)).scalar_subquery().label("total_libros"),
        select(func.coalesce(func.sum(Libro.ejemplares), 0)).scalar_subquery().label("total_ejemplares"),
        select(func.count(Prestamo.id)).where(Prestamo.fecha_devolucion.is_(None)).scalar_subquery().label("total_prestados"),
        select(func.count(Socio.id)).where(Socio.activo.is_(True)).scalar_subquery().label("socios_activos"),
        select(func.count(Prestamo.id)).where(
            Prestamo.fecha_devolucion.is_(None),
            Prestamo.fecha_limite < func.current_date(),
        ).scalar_subquery().label("prestamos_vencidos"),
        select(func.coalesce(func.sum(Prestamo.multa), Decimal("0.00"))).scalar_subquery().label("total_multas"),
    )
    fila = db.execute(stmt).mappings().one()
    return ResumenReporte.model_validate(dict(fila))
