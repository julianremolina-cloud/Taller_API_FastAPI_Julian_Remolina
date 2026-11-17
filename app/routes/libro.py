from typing import Optional
from fastapi import APIRouter, Query, Response, status

from ..controllers import libro as libro_controller
from ..core.dependencies import PaginacionDep, SessionDep, requiere_rol
from ..models.usuario import RolUsuario
from ..schemas.libro import LibroCreate, LibroResponse, LibroUpdate, OrdenLibrosEnum
from ..schemas.pagina import Pagina

router = APIRouter(prefix="/libros", tags=["Libros"])


@router.get(
    "",
    response_model=Pagina[LibroResponse],
    summary="Listado paginado de libros",
    responses={200: {"description": "Listado de libros con total"}},
)
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


@router.get(
    "/{id}",
    response_model=LibroResponse,
    summary="Consulta detalle de un libro",
    responses={
        200: {"description": "Detalle del libro"},
        404: {"description": "Libro no encontrado"},
    },
)
def obtener_libro(id: int, db: SessionDep):
    """Consulta un libro por su ID con autor, categorías y disponibles calculados."""
    return libro_controller.obtener_libro_por_id(db=db, libro_id=id)


@router.post(
    "",
    response_model=LibroResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[requiere_rol(RolUsuario.admin, RolUsuario.bibliotecario)],
    summary="Crear un nuevo libro",
    responses={
        201: {"description": "Libro creado exitosamente"},
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
        404: {"description": "Autor o categoría no encontrados"},
        409: {"description": "ISBN duplicado"},
    },
)
def crear_libro(libro_in: LibroCreate, db: SessionDep):
    """Crea un nuevo libro (404 si autor o categoría no existen; 409 si ISBN existe)."""
    return libro_controller.crear_libro(db=db, libro_in=libro_in)


@router.patch(
    "/{id}",
    response_model=LibroResponse,
    dependencies=[requiere_rol(RolUsuario.admin, RolUsuario.bibliotecario)],
    summary="Actualizar un libro existente",
    responses={
        200: {"description": "Libro actualizado exitosamente"},
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
        404: {"description": "Libro no encontrado"},
        409: {"description": "ISBN duplicado"},
        422: {"description": "Ejemplares por debajo de préstamos activos"},
    },
)
def actualizar_libro(id: int, libro_in: LibroUpdate, db: SessionDep):
    """Actualiza un libro. 422 si ejemplares queda por debajo de préstamos activos."""
    return libro_controller.actualizar_libro(db=db, libro_id=id, libro_in=libro_in)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[requiere_rol(RolUsuario.admin)],
    summary="Eliminar un libro",
    responses={
        204: {"description": "Libro eliminado"},
        401: {"description": "No autenticado"},
        403: {"description": "Solo el administrador puede eliminar"},
        404: {"description": "Libro no encontrado"},
        409: {"description": "No se puede eliminar porque tiene préstamos activos"},
    },
)
def eliminar_libro(id: int, db: SessionDep):
    """Elimina un libro si no tiene préstamos activos."""
    libro_controller.eliminar_libro(db=db, libro_id=id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
