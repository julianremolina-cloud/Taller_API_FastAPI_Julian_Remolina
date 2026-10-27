from sqlalchemy import func, select
from sqlalchemy.orm import Session
from ..core.exceptions import Conflicto, NoEncontrado
from ..models.categoria import Categoria
from ..schemas.categoria import CategoriaCreate, CategoriaUpdate


def listar_categorias(db: Session, skip: int, limit: int) -> list[Categoria]:
    """Lista las categorías con paginación."""
    query = select(Categoria).order_by(Categoria.id.asc()).offset(skip).limit(limit)
    return list(db.scalars(query).all())


def obtener_categoria_por_id(db: Session, categoria_id: int) -> Categoria:
    """Obtiene una categoría por ID o lanza 404 si no existe."""
    categoria = db.get(Categoria, categoria_id)
    if not categoria:
        raise NoEncontrado(f"Categoría con ID {categoria_id} no encontrada")
    return categoria


def crear_categoria(db: Session, categoria_in: CategoriaCreate) -> Categoria:
    """Crea una categoría verificando que el nombre no esté duplicado."""
    existente = db.scalar(
        select(Categoria).where(func.lower(Categoria.nombre) == func.lower(categoria_in.nombre))
    )
    if existente:
        raise Conflicto(f"La categoría '{categoria_in.nombre}' ya existe")

    categoria = Categoria(
        nombre=categoria_in.nombre,
        descripcion=categoria_in.descripcion,
    )
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria


def actualizar_categoria(
    db: Session,
    categoria_id: int,
    categoria_in: CategoriaUpdate,
) -> Categoria:
    """Actualiza una categoría."""
    categoria = obtener_categoria_por_id(db, categoria_id)
    datos = categoria_in.model_dump(exclude_unset=True)

    if "nombre" in datos and datos["nombre"]:
        existente = db.scalar(
            select(Categoria).where(
                func.lower(Categoria.nombre) == func.lower(datos["nombre"]),
                Categoria.id != categoria_id,
            )
        )
        if existente:
            raise Conflicto(f"Ya existe otra categoría con el nombre '{datos['nombre']}'")

    for campo, valor in datos.items():
        setattr(categoria, campo, valor)

    db.commit()
    db.refresh(categoria)
    return categoria


def eliminar_categoria(db: Session, categoria_id: int) -> None:
    """Elimina una categoría y la desvincula de los libros que la tenían."""
    categoria = obtener_categoria_por_id(db, categoria_id)
    categoria.libros = []
    db.delete(categoria)
    db.commit()
