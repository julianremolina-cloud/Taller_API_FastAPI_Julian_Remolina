from fastapi import APIRouter, Response, status
from ..core.dependencies import PaginacionDep, SessionDep
from ..controllers import categoria as categoria_controller
from ..schemas.categoria import CategoriaCreate, CategoriaResponse, CategoriaUpdate

router = APIRouter(prefix="/categorias", tags=["Categorías"])


@router.get("", response_model=list[CategoriaResponse])
def listar_categorias(db: SessionDep, pag: PaginacionDep):
    """Lista las categorías con paginación."""
    return categoria_controller.listar_categorias(
        db=db,
        skip=pag.skip,
        limit=pag.limit,
    )


@router.get("/{id}", response_model=CategoriaResponse)
def obtener_categoria(id: int, db: SessionDep):
    """Consulta una categoría por su ID (404 si no existe)."""
    return categoria_controller.obtener_categoria_por_id(db=db, categoria_id=id)


@router.post("", response_model=CategoriaResponse, status_code=status.HTTP_201_CREATED)
def crear_categoria(categoria_in: CategoriaCreate, db: SessionDep):
    """Crea una categoría (409 si ya existe)."""
    return categoria_controller.crear_categoria(db=db, categoria_in=categoria_in)


@router.patch("/{id}", response_model=CategoriaResponse)
def actualizar_categoria(id: int, categoria_in: CategoriaUpdate, db: SessionDep):
    """Actualiza una categoría."""
    return categoria_controller.actualizar_categoria(
        db=db,
        categoria_id=id,
        categoria_in=categoria_in,
    )


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_categoria(id: int, db: SessionDep):
    """Elimina una categoría; se desvincula de los libros que la tenían."""
    categoria_controller.eliminar_categoria(db=db, categoria_id=id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
