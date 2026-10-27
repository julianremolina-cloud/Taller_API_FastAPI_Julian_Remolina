from typing import Optional
from fastapi import APIRouter, Query, Response, status
from ..core.dependencies import PaginacionDep, SessionDep
from ..controllers import libro as libro_controller
from ..schemas.libro import LibroCreate, LibroResponse, LibroUpdate, OrdenLibrosEnum

router = APIRouter(prefix="/libros", tags=["Libros"])


@router.get("", response_model=list[LibroResponse])
def listar_libros(
    db: SessionDep,
    pag: PaginacionDep,
    buscar: Optional[str] = Query(None, description="Buscar por título (ilike)"),
    autor: Optional[str] = Query(None, description="Buscar por nombre de autor"),
    categoria_id: Optional[int] = Query(None, description="Filtrar por ID de categoría"),
    desde: Optional[int] = Query(None, description="Año de publicación mínimo"),
    hasta: Optional[int] = Query(None, description="Año de publicación máximo"),
    orden: Optional[OrdenLibrosEnum] = Query(None, description="Ordenamiento (titulo, anio, -anio)"),
):
    """Lista libros con filtros combinables, ordenamiento y paginación."""
    return libro_controller.listar_libros(
        db=db,
        skip=pag.skip,
        limit=pag.limit,
        buscar=buscar,
        autor=autor,
        categoria_id=categoria_id,
        desde=desde,
        hasta=hasta,
        orden=orden,
    )


@router.get("/{id}", response_model=LibroResponse)
def obtener_libro(id: int, db: SessionDep):
    """Consulta un libro por su ID con autor, categorías y disponibles calculados."""
    return libro_controller.obtener_libro_por_id(db=db, libro_id=id)


@router.post("", response_model=LibroResponse, status_code=status.HTTP_201_CREATED)
def crear_libro(libro_in: LibroCreate, db: SessionDep):
    """Crea un nuevo libro (404 si autor o categoría no existen; 409 si ISBN existe)."""
    return libro_controller.crear_libro(db=db, libro_in=libro_in)


@router.patch("/{id}", response_model=LibroResponse)
def actualizar_libro(id: int, libro_in: LibroUpdate, db: SessionDep):
    """Actualiza un libro. 422 si ejemplares queda por debajo de préstamos activos."""
    return libro_controller.actualizar_libro(db=db, libro_id=id, libro_in=libro_in)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_libro(id: int, db: SessionDep):
    """Elimina un libro (409 si tiene préstamos sin devolver)."""
    libro_controller.eliminar_libro(db=db, libro_id=id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
