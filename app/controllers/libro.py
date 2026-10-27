from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from ..core.exceptions import Conflicto, NoEncontrado, ReglaNegocio
from ..models.autor import Autor
from ..models.categoria import Categoria
from ..models.libro import Libro
from ..models.prestamo import Prestamo
from ..schemas.libro import LibroCreate, LibroUpdate, OrdenLibrosEnum


def _calcular_disponibles_varios(db: Session, libros: list[Libro]) -> None:
    """Calcula y asigna el atributo 'disponibles' a una lista de libros."""
    if not libros:
        return
    libro_ids = [l.id for l in libros]
    prestamos_activos_query = (
        select(Prestamo.libro_id, func.count(Prestamo.id))
        .where(
            Prestamo.libro_id.in_(libro_ids),
            Prestamo.fecha_devolucion.is_(None),
        )
        .group_by(Prestamo.libro_id)
    )
    activos_dict = dict(db.execute(prestamos_activos_query).all())
    for libro in libros:
        prestados = activos_dict.get(libro.id, 0)
        libro.disponibles = max(0, libro.ejemplares - prestados)


def _calcular_disponibles_uno(db: Session, libro: Libro) -> None:
    """Calcula y asigna el atributo 'disponibles' a un libro."""
    prestados = db.scalar(
        select(func.count(Prestamo.id)).where(
            Prestamo.libro_id == libro.id,
            Prestamo.fecha_devolucion.is_(None),
        )
    ) or 0
    libro.disponibles = max(0, libro.ejemplares - prestados)


def listar_libros(
    db: Session,
    skip: int,
    limit: int,
    buscar: Optional[str] = None,
    autor: Optional[str] = None,
    categoria_id: Optional[int] = None,
    desde: Optional[int] = None,
    hasta: Optional[int] = None,
    orden: Optional[OrdenLibrosEnum] = None,
) -> list[Libro]:
    """Lista libros con filtros combinables, ordenamiento y carga optimizada."""
    consulta = select(Libro).options(
        selectinload(Libro.autor),
        selectinload(Libro.categorias),
    )

    if buscar:
        consulta = consulta.where(Libro.titulo.ilike(f"%{buscar.strip()}%"))
    if autor:
        consulta = consulta.join(Libro.autor).where(Autor.nombre.ilike(f"%{autor.strip()}%"))
    if categoria_id:
        consulta = consulta.join(Libro.categorias).where(Categoria.id == categoria_id)
    if desde is not None:
        consulta = consulta.where(Libro.anio_publicacion >= desde)
    if hasta is not None:
        consulta = consulta.where(Libro.anio_publicacion <= hasta)

    # Ordenamiento
    if orden == OrdenLibrosEnum.titulo:
        consulta = consulta.order_by(Libro.titulo.asc())
    elif orden == OrdenLibrosEnum.anio:
        consulta = consulta.order_by(Libro.anio_publicacion.asc())
    elif orden == OrdenLibrosEnum.menos_anio:
        consulta = consulta.order_by(Libro.anio_publicacion.desc())
    else:
        consulta = consulta.order_by(Libro.id.asc())

    libros = list(db.scalars(consulta.offset(skip).limit(limit)).all())
    _calcular_disponibles_varios(db, libros)
    return libros


def obtener_libro_por_id(db: Session, libro_id: int) -> Libro:
    """Obtiene un libro por su ID con autor y categorías anidados."""
    consulta = (
        select(Libro)
        .options(selectinload(Libro.autor), selectinload(Libro.categorias))
        .where(Libro.id == libro_id)
    )
    libro = db.scalar(consulta)
    if not libro:
        raise NoEncontrado(f"Libro con ID {libro_id} no encontrado")
    _calcular_disponibles_uno(db, libro)
    return libro


def crear_libro(db: Session, libro_in: LibroCreate) -> Libro:
    """Crea un nuevo libro verificando autor, categorías y unicidad de ISBN."""
    # Verificar autor
    autor = db.get(Autor, libro_in.autor_id)
    if not autor:
        raise NoEncontrado(f"Autor con ID {libro_in.autor_id} no encontrado")

    # Verificar categorías
    categorias = list(
        db.scalars(
            select(Categoria).where(Categoria.id.in_(libro_in.categoria_ids))
        ).all()
    )
    if len(categorias) != len(libro_in.categoria_ids):
        raise NoEncontrado("Una o más categorías especificadas no existen")

    # Verificar ISBN único
    existente_isbn = db.scalar(
        select(Libro).where(Libro.isbn == libro_in.isbn)
    )
    if existente_isbn:
        raise Conflicto(f"El ISBN '{libro_in.isbn}' ya está registrado")

    libro = Libro(
        titulo=libro_in.titulo,
        isbn=libro_in.isbn,
        anio_publicacion=libro_in.anio_publicacion,
        ejemplares=libro_in.ejemplares,
        autor_id=libro_in.autor_id,
    )
    libro.categorias = categorias
    db.add(libro)
    db.commit()
    db.refresh(libro)

    # Cargar relaciones para la respuesta
    return obtener_libro_por_id(db, libro.id)


def actualizar_libro(db: Session, libro_id: int, libro_in: LibroUpdate) -> Libro:
    """Actualiza un libro verificando dependencias y reglas de negocio."""
    libro = obtener_libro_por_id(db, libro_id)
    datos = libro_in.model_dump(exclude_unset=True)

    if "autor_id" in datos and datos["autor_id"] is not None:
        autor = db.get(Autor, datos["autor_id"])
        if not autor:
            raise NoEncontrado(f"Autor con ID {datos['autor_id']} no encontrado")
        libro.autor_id = datos["autor_id"]

    if "isbn" in datos and datos["isbn"]:
        existente = db.scalar(
            select(Libro).where(Libro.isbn == datos["isbn"], Libro.id != libro_id)
        )
        if existente:
            raise Conflicto(f"El ISBN '{datos['isbn']}' ya está registrado por otro libro")
        libro.isbn = datos["isbn"]

    if "categoria_ids" in datos and datos["categoria_ids"] is not None:
        categorias = list(
            db.scalars(
                select(Categoria).where(Categoria.id.in_(datos["categoria_ids"]))
            ).all()
        )
        if len(categorias) != len(datos["categoria_ids"]):
            raise NoEncontrado("Una o más categorías especificadas no existen")
        libro.categorias = categorias

    if "ejemplares" in datos and datos["ejemplares"] is not None:
        prestamos_activos = db.scalar(
            select(func.count(Prestamo.id)).where(
                Prestamo.libro_id == libro_id,
                Prestamo.fecha_devolucion.is_(None),
            )
        ) or 0
        if datos["ejemplares"] < prestamos_activos:
            raise ReglaNegocio(
                f"Los ejemplares ({datos['ejemplares']}) no pueden quedar por debajo de los préstamos activos ({prestamos_activos})"
            )
        libro.ejemplares = datos["ejemplares"]

    if "titulo" in datos and datos["titulo"]:
        libro.titulo = datos["titulo"]
    if "anio_publicacion" in datos and datos["anio_publicacion"] is not None:
        libro.anio_publicacion = datos["anio_publicacion"]

    db.commit()
    return obtener_libro_por_id(db, libro.id)


def eliminar_libro(db: Session, libro_id: int) -> None:
    """Elimina un libro si no tiene préstamos sin devolver (409 en caso contrario)."""
    libro = obtener_libro_por_id(db, libro_id)

    prestamos_sin_devolver = db.scalar(
        select(func.count(Prestamo.id)).where(
            Prestamo.libro_id == libro_id,
            Prestamo.fecha_devolucion.is_(None),
        )
    ) or 0
    if prestamos_sin_devolver > 0:
        raise Conflicto(
            f"No se puede eliminar el libro porque tiene {prestamos_sin_devolver} préstamos sin devolver"
        )

    db.delete(libro)
    db.commit()


def listar_libros_por_autor(db: Session, autor_id: int) -> list[Libro]:
    """Lista los libros pertenecientes a un autor específico."""
    autor = db.get(Autor, autor_id)
    if not autor:
        raise NoEncontrado(f"Autor con ID {autor_id} no encontrado")

    consulta = (
        select(Libro)
        .options(selectinload(Libro.autor), selectinload(Libro.categorias))
        .where(Libro.autor_id == autor_id)
        .order_by(Libro.id.asc())
    )
    libros = list(db.scalars(consulta).all())
    _calcular_disponibles_varios(db, libros)
    return libros
