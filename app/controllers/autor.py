from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core.exceptions import Conflicto, NoEncontrado
from ..models.autor import Autor
from ..models.libro import Libro
from ..schemas.autor import AutorCreate, AutorResponse, AutorUpdate
from ..schemas.pagina import Pagina


def listar_autores(
    db: Session,
    skip: int,
    limit: int,
    nacionalidad: Optional[str] = None,
) -> Pagina[AutorResponse]:
    """Lista autores con paginación y filtro opcional por nacionalidad."""
    query = select(Autor)
    if nacionalidad:
        query = query.where(Autor.nacionalidad.ilike(f"%{nacionalidad.strip()}%"))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = list(db.scalars(query.order_by(Autor.id.asc()).offset(skip).limit(limit)).all())
    return Pagina[AutorResponse](
        items=[AutorResponse.model_validate(a) for a in items],
        total=total,
        skip=skip,
        limit=limit,
    )


def obtener_autor_por_id(db: Session, autor_id: int) -> Autor:
    """Obtiene un autor por su ID o lanza 404 si no existe."""
    autor = db.get(Autor, autor_id)
    if not autor:
        raise NoEncontrado(f"Autor con ID {autor_id} no encontrado")
    return autor


def crear_autor(db: Session, autor_in: AutorCreate) -> Autor:
    """Crea un autor comprobando que el nombre no esté duplicado."""
    existente = db.scalar(
        select(Autor).where(func.lower(Autor.nombre) == func.lower(autor_in.nombre))
    )
    if existente:
        raise Conflicto(f"El autor con el nombre '{autor_in.nombre}' ya existe")

    autor = Autor(
        nombre=autor_in.nombre,
        nacionalidad=autor_in.nacionalidad,
        anio_nacimiento=autor_in.anio_nacimiento,
    )
    db.add(autor)
    db.commit()
    db.refresh(autor)
    return autor


def actualizar_autor(db: Session, autor_id: int, autor_in: AutorUpdate) -> Autor:
    """Actualiza parcialmente un autor comprobando unicidad del nombre si cambia."""
    autor = obtener_autor_por_id(db, autor_id)

    if autor_in.nombre is not None and autor_in.nombre != autor.nombre:
        existente = db.scalar(
            select(Autor).where(
                func.lower(Autor.nombre) == func.lower(autor_in.nombre),
                Autor.id != autor_id,
            )
        )
        if existente:
            raise Conflicto(f"Ya existe otro autor con el nombre '{autor_in.nombre}'")
        autor.nombre = autor_in.nombre

    if autor_in.nacionalidad is not None:
        autor.nacionalidad = autor_in.nacionalidad
    if autor_in.anio_nacimiento is not None:
        autor.anio_nacimiento = autor_in.anio_nacimiento

    db.commit()
    db.refresh(autor)
    return autor


def eliminar_autor(db: Session, autor_id: int) -> None:
    """Elimina un autor o lanza 409 si tiene libros asociados."""
    autor = obtener_autor_por_id(db, autor_id)

    libros_asociados = db.scalar(
        select(func.count(Libro.id)).where(Libro.autor_id == autor_id)
    ) or 0
    if libros_asociados > 0:
        raise Conflicto(f"No se puede eliminar el autor porque tiene {libros_asociados} libro(s) asociado(s)")

    db.delete(autor)
    db.commit()
