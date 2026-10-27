from typing import Optional
from fastapi import APIRouter, Query, status
from ..core.dependencies import PaginacionDep, SessionDep
from ..controllers import prestamo as prestamo_controller
from ..schemas.prestamo import (
    DevolucionCreate,
    PrestamoCreate,
    PrestamoDetalleResponse,
    PrestamoResponse,
)

router = APIRouter(prefix="/prestamos", tags=["Préstamos"])


@router.get("", response_model=list[PrestamoResponse])
def listar_prestamos(
    db: SessionDep,
    pag: PaginacionDep,
    estado: Optional[str] = Query(None, description="Filtrar por estado: activo, vencido, devuelto"),
    socio_id: Optional[int] = Query(None, description="Filtrar por ID de socio"),
    libro_id: Optional[int] = Query(None, description="Filtrar por ID de libro"),
):
    """Lista préstamos paginados con filtros opcionales."""
    return prestamo_controller.listar_prestamos(
        db=db,
        skip=pag.skip,
        limit=pag.limit,
        estado=estado,
        socio_id=socio_id,
        libro_id=libro_id,
    )


@router.get("/{id}", response_model=PrestamoDetalleResponse)
def obtener_prestamo(id: int, db: SessionDep):
    """Consulta un préstamo por su ID con el libro y el socio anidados."""
    return prestamo_controller.obtener_prestamo_por_id(db=db, prestamo_id=id)


@router.post("", response_model=PrestamoResponse, status_code=status.HTTP_201_CREATED)
def crear_prestamo(prestamo_in: PrestamoCreate, db: SessionDep):
    """Registra un préstamo aplicando las reglas R1 a R8."""
    return prestamo_controller.registrar_prestamo(db=db, prestamo_in=prestamo_in)


@router.post("/{id}/devolucion", response_model=PrestamoResponse)
def registrar_devolucion(
    id: int,
    devolucion_in: DevolucionCreate,
    db: SessionDep,
):
    """Registra la devolución de un préstamo aplicando las reglas R9 y R10."""
    return prestamo_controller.registrar_devolucion(
        db=db,
        prestamo_id=id,
        devolucion_in=devolucion_in,
    )
