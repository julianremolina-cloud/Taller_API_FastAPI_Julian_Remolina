from typing import Optional
from fastapi import APIRouter, Query, Response, status

from ..controllers import autor as autor_controller
from ..core.dependencies import PaginacionDep, SessionDep, requiere_rol
from ..models.usuario import RolUsuario
from ..schemas.autor import AutorCreate, AutorResponse, AutorUpdate
from ..schemas.pagina import Pagina

router = APIRouter(prefix="/autores", tags=["Autores"])


@router.get(
    "",
    response_model=Pagina[AutorResponse],
    summary="Listado paginado de autores",
    responses={200: {"description": "Listado de autores con total"}},
)
def listar_autores(
    db: SessionDep,
    pag: PaginacionDep,
    nacionalidad: Optional[str] = Query(None, description="Filtrar por nacionalidad del autor"),
):
    """Lista paginada de autores con filtro opcional por nacionalidad."""
    return autor_controller.listar_autores(
        db=db,
        skip=pag.skip,
        limit=pag.limit,
        nacionalidad=nacionalidad,
    )


@router.get(
    "/{id}",
    response_model=AutorResponse,
    summary="Consulta detalle de un autor",
    responses={
        200: {"description": "Detalle del autor"},
        404: {"description": "Autor no encontrado"},
    },
)
def obtener_autor(id: int, db: SessionDep):
    """Consulta un autor por su ID."""
    return autor_controller.obtener_autor_por_id(db=db, autor_id=id)


@router.post(
    "",
    response_model=AutorResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[requiere_rol(RolUsuario.admin, RolUsuario.bibliotecario)],
    summary="Crear un nuevo autor",
    responses={
        201: {"description": "Autor creado exitosamente"},
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
        409: {"description": "Nombre de autor ya existente"},
    },
)
def crear_autor(autor_in: AutorCreate, db: SessionDep):
    """Crea un nuevo autor en la base de datos."""
    return autor_controller.crear_autor(db=db, autor_in=autor_in)


@router.patch(
    "/{id}",
    response_model=AutorResponse,
    dependencies=[requiere_rol(RolUsuario.admin, RolUsuario.bibliotecario)],
    summary="Actualizar un autor existente",
    responses={
        200: {"description": "Autor actualizado exitosamente"},
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
        404: {"description": "Autor no encontrado"},
        409: {"description": "Nombre de autor duplicado"},
    },
)
def actualizar_autor(id: int, autor_in: AutorUpdate, db: SessionDep):
    """Actualiza parcialmente un autor."""
    return autor_controller.actualizar_autor(db=db, autor_id=id, autor_in=autor_in)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[requiere_rol(RolUsuario.admin)],
    summary="Eliminar un autor",
    responses={
        204: {"description": "Autor eliminado"},
        401: {"description": "No autenticado"},
        403: {"description": "Solo el administrador puede eliminar"},
        404: {"description": "Autor no encontrado"},
        409: {"description": "No se puede eliminar porque tiene libros asociados"},
    },
)
def eliminar_autor(id: int, db: SessionDep):
    """Elimina un autor si no tiene libros asociados."""
    autor_controller.eliminar_autor(db=db, autor_id=id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
