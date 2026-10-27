from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from ..core.exceptions import Conflicto, NoEncontrado
from ..models.autor import Autor
from ..models.libro import Libro
from ..schemas.autor import AutorCreate, AutorUpdate


def listar_autores(
    db: Session,
    skip: int,
    limit: int,
    nacionalidad: Optional[str] = None,
) -> list[Autor]:
    """Lista autores con paginación y filtro opcional por nacionalidad."""
    query = select(Autor)
    if nacionalidad:
        query = query.where(Autor.nacionalidad.ilike(f"%{nacionalidad.strip()}%"))
    query = query.order_by(Autor.id.asc()).offset(skip).limit(limit)
    return list(db.scalars(query).all())


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
    """Actualiza solo los campos enviados para el autor."""
    autor = obtener_autor_por_id(db, autor_id)
    datos = autor_in.model_dump(exclude_unset=True)

    if "nombre" in datos and datos["nombre"]:
        existente = db.scalar(
            select(Autor).where(
                func.lower(Autor.nombre) == func.lower(datos["nombre"]),
                Autor.id != autor_id,
            )
        )
        if existente:
            raise Conflicto(f"Ya existe otro autor con el nombre '{datos['nombre']}'")

    for campo, valor in datos.items():
        setattr(autor, campo, valor)

    db.commit()
    db.refresh(autor)
    return autor


def eliminar_autor(db: Session, autor_id: int) -> None:
    """Elimina un autor si no tiene libros asociados (409 en caso contrario)."""
    autor = obtener_autor_por_id(db, autor_id)

    total_libros = db.scalar(
        select(func.count(Libro.id)).where(Libro.autor_id == autor_id)
    )
    if total_libros and total_libros > 0:
        raise Conflicto("No se puede eliminar el autor porque tiene libros asociados")

    db.delete(autor)
    db.commit()
