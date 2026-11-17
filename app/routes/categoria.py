from fastapi import APIRouter, Response, status

from ..controllers import categoria as categoria_controller
from ..core.dependencies import PaginacionDep, SessionDep, requiere_rol
from ..models.usuario import RolUsuario
from ..schemas.categoria import CategoriaCreate, CategoriaResponse, CategoriaUpdate
from ..schemas.pagina import Pagina

router = APIRouter(prefix="/categorias", tags=["Categorías"])


@router.get(
    "",
    response_model=Pagina[CategoriaResponse],
    summary="Listado paginado de categorías",
    responses={200: {"description": "Listado de categorías con total"}},
)
def listar_categorias(db: SessionDep, pag: PaginacionDep):
    """Lista las categorías con paginación."""
    return categoria_controller.listar_categorias(
        db=db,
        skip=pag.skip,
        limit=pag.limit,
    )


@router.get(
    "/{id}",
    response_model=CategoriaResponse,
    summary="Consulta detalle de una categoría",
    responses={
        200: {"description": "Detalle de la categoría"},
        404: {"description": "Categoría no encontrada"},
    },
)
def obtener_categoria(id: int, db: SessionDep):
    """Consulta una categoría por su ID."""
    return categoria_controller.obtener_categoria_por_id(db=db, categoria_id=id)


@router.post(
    "",
    response_model=CategoriaResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[requiere_rol(RolUsuario.admin, RolUsuario.bibliotecario)],
    summary="Crear una nueva categoría",
    responses={
        201: {"description": "Categoría creada exitosamente"},
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
        409: {"description": "Nombre de categoría duplicado"},
    },
)
def crear_categoria(categoria_in: CategoriaCreate, db: SessionDep):
    """Crea una nueva categoría."""
    return categoria_controller.crear_categoria(db=db, categoria_in=categoria_in)


@router.patch(
    "/{id}",
    response_model=CategoriaResponse,
    dependencies=[requiere_rol(RolUsuario.admin, RolUsuario.bibliotecario)],
    summary="Actualizar una categoría",
    responses={
        200: {"description": "Categoría actualizada exitosamente"},
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
        404: {"description": "Categoría no encontrada"},
        409: {"description": "Nombre de categoría duplicado"},
    },
)
def actualizar_categoria(
    id: int,
    categoria_in: CategoriaUpdate,
    db: SessionDep,
):
    """Actualiza una categoría existente."""
    return categoria_controller.actualizar_categoria(db=db, categoria_id=id, categoria_in=categoria_in)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[requiere_rol(RolUsuario.admin)],
    summary="Eliminar una categoría",
    responses={
        204: {"description": "Categoría eliminada"},
        401: {"description": "No autenticado"},
        403: {"description": "Solo el administrador puede eliminar"},
        404: {"description": "Categoría no encontrada"},
    },
)
def eliminar_categoria(id: int, db: SessionDep):
    """Elimina una categoría desvinculándola de los libros asociados."""
    categoria_controller.eliminar_categoria(db=db, categoria_id=id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
