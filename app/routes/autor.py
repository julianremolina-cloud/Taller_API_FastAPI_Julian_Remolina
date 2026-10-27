from typing import Optional
from fastapi import APIRouter, Query, Response, status
from ..core.dependencies import PaginacionDep, SessionDep
from ..controllers import autor as autor_controller
from ..controllers import libro as libro_controller
from ..schemas.autor import AutorCreate, AutorResponse, AutorUpdate
from ..schemas.libro import LibroResponse

router = APIRouter(prefix="/autores", tags=["Autores"])


@router.get("", response_model=list[AutorResponse])
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


@router.get("/{id}", response_model=AutorResponse)
def obtener_autor(id: int, db: SessionDep):
    """Consulta un autor por su ID (404 si no existe)."""
    return autor_controller.obtener_autor_por_id(db=db, autor_id=id)


@router.get("/{id}/libros", response_model=list[LibroResponse])
def listar_libros_de_autor(id: int, db: SessionDep):
    """Lista todos los libros pertenecientes a un autor específico."""
    return libro_controller.listar_libros_por_autor(db=db, autor_id=id)


@router.post("", response_model=AutorResponse, status_code=status.HTTP_201_CREATED)
def crear_autor(autor_in: AutorCreate, db: SessionDep):
    """Crea un autor (409 si el nombre ya existe)."""
    return autor_controller.crear_autor(db=db, autor_in=autor_in)


@router.patch("/{id}", response_model=AutorResponse)
def actualizar_autor(id: int, autor_in: AutorUpdate, db: SessionDep):
    """Actualiza solo los campos enviados de un autor."""
    return autor_controller.actualizar_autor(db=db, autor_id=id, autor_in=autor_in)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_autor(id: int, db: SessionDep):
    """Elimina un autor (409 si tiene libros)."""
    autor_controller.eliminar_autor(db=db, autor_id=id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
