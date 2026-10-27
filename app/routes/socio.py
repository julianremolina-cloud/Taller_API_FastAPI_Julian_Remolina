from typing import Optional
from fastapi import APIRouter, Query, Response, status
from ..core.dependencies import PaginacionDep, SessionDep
from ..controllers import socio as socio_controller
from ..schemas.prestamo import PrestamoResponse
from ..schemas.socio import SocioCreate, SocioResponse, SocioUpdate

router = APIRouter(prefix="/socios", tags=["Socios"])


@router.get("", response_model=list[SocioResponse])
def listar_socios(
    db: SessionDep,
    pag: PaginacionDep,
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo (true/false)"),
):
    """Lista paginada de socios con filtro opcional por estado activo."""
    return socio_controller.listar_socios(
        db=db,
        skip=pag.skip,
        limit=pag.limit,
        activo=activo,
    )


@router.get("/{id}", response_model=SocioResponse)
def obtener_socio(id: int, db: SessionDep):
    """Consulta un socio por su ID (404 si no existe)."""
    return socio_controller.obtener_socio_por_id(db=db, socio_id=id)


@router.get("/{id}/prestamos", response_model=list[PrestamoResponse])
def listar_prestamos_de_socio(
    id: int,
    db: SessionDep,
    estado: Optional[str] = Query(None, description="Filtrar por estado: activo, vencido o devuelto"),
):
    """Lista los préstamos de un socio con filtro opcional por estado."""
    return socio_controller.listar_prestamos_socio(db=db, socio_id=id, estado=estado)


@router.post("", response_model=SocioResponse, status_code=status.HTTP_201_CREATED)
def crear_socio(socio_in: SocioCreate, db: SessionDep):
    """Crea un nuevo socio (409 si el email ya existe)."""
    return socio_controller.crear_socio(db=db, socio_in=socio_in)


@router.patch("/{id}", response_model=SocioResponse)
def actualizar_socio(id: int, socio_in: SocioUpdate, db: SessionDep):
    """Actualiza los datos de un socio."""
    return socio_controller.actualizar_socio(db=db, socio_id=id, socio_in=socio_in)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_socio(id: int, db: SessionDep):
    """
    Elimina un socio:
    - 409 si tiene préstamos sin devolver.
    - Se desactiva si solo tiene préstamos devueltos.
    - Se elimina físicamente si no tiene préstamos.
    """
    socio_controller.eliminar_socio(db=db, socio_id=id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
