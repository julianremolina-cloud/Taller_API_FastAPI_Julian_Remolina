from typing import Optional
from fastapi import APIRouter, Depends, Query, status

from ..controllers import prestamo as prestamo_controller
from ..core.dependencies import CurrentUser, PaginacionDep, SessionDep, requiere_rol
from ..models.usuario import RolUsuario
from ..schemas.pagina import Pagina
from ..schemas.prestamo import (
    DevolucionCreate,
    PrestamoCreate,
    PrestamoDetalleResponse,
    PrestamoResponse,
)

router = APIRouter(prefix="/prestamos", tags=["Préstamos"])


@router.get(
    "",
    response_model=Pagina[PrestamoResponse],
    summary="Listado paginado de préstamos",
    responses={
        200: {"description": "Listado de préstamos"},
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
    },
)
def listar_prestamos(
    db: SessionDep,
    pag: PaginacionDep,
    usuario: CurrentUser,
    estado: Optional[str] = Query(None, description="Filtrar por estado: activo, vencido, devuelto"),
    socio_id: Optional[int] = Query(None, description="Filtrar por ID de socio"),
    libro_id: Optional[int] = Query(None, description="Filtrar por ID de libro"),
):
    """Lista préstamos paginados con filtros opcionales. Los socios solo ven sus propios préstamos."""
    return prestamo_controller.listar_prestamos(
        db=db,
        skip=pag.skip,
        limit=pag.limit,
        usuario=usuario,
        estado=estado,
        socio_id=socio_id,
        libro_id=libro_id,
    )


@router.get(
    "/{id}",
    response_model=PrestamoDetalleResponse,
    summary="Consulta detalle de un préstamo",
    responses={
        200: {"description": "Detalle del préstamo con libro y socio"},
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes"},
        404: {"description": "Préstamo no encontrado"},
    },
)
def obtener_prestamo(
    id: int,
    db: SessionDep,
    usuario: CurrentUser,
):
    """Consulta un préstamo por ID. Si es socio y no es suyo, retorna 404 (regla Z2)."""
    return prestamo_controller.obtener_prestamo_por_id(db=db, prestamo_id=id, usuario=usuario)


@router.post(
    "",
    response_model=PrestamoResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[requiere_rol(RolUsuario.admin, RolUsuario.bibliotecario)],
    summary="Registro de préstamo",
    responses={
        201: {"description": "Préstamo registrado exitosamente"},
        401: {"description": "No autenticado"},
        403: {"description": "Solo staff (bibliotecario o admin)"},
        404: {"description": "Socio o libro no encontrado"},
        409: {"description": "Libro ya prestado al socio"},
        422: {"description": "Socio inactivo, con préstamos vencidos, multas o sin ejemplares"},
    },
)
def crear_prestamo(
    prestamo_in: PrestamoCreate,
    db: SessionDep,
    usuario: CurrentUser,
):
    """Registra un nuevo préstamo y almacena la auditoría de quién lo registró (Z7)."""
    return prestamo_controller.registrar_prestamo(
        db=db,
        prestamo_in=prestamo_in,
        usuario_actual=usuario,
    )


@router.post(
    "/{id}/devolucion",
    response_model=PrestamoResponse,
    dependencies=[requiere_rol(RolUsuario.admin, RolUsuario.bibliotecario)],
    summary="Registro de devolución de un préstamo",
    responses={
        200: {"description": "Devolución registrada exitosamente"},
        401: {"description": "No autenticado"},
        403: {"description": "Solo staff (bibliotecario o admin)"},
        404: {"description": "Préstamo no encontrado"},
        409: {"description": "El préstamo ya fue devuelto"},
        422: {"description": "Fecha de devolución anterior a la de préstamo"},
    },
)
def registrar_devolucion(
    id: int,
    devolucion_in: DevolucionCreate,
    db: SessionDep,
):
    """Registra la devolución calculando multas en caso de retraso."""
    return prestamo_controller.registrar_devolucion(
        db=db,
        prestamo_id=id,
        devolucion_in=devolucion_in,
    )


@router.post(
    "/{id}/pago-multa",
    response_model=PrestamoResponse,
    dependencies=[requiere_rol(RolUsuario.admin, RolUsuario.bibliotecario)],
    summary="Pago de multa de un préstamo",
    responses={
        200: {"description": "Multa pagada exitosamente"},
        401: {"description": "No autenticado"},
        403: {"description": "Solo staff (bibliotecario o admin)"},
        404: {"description": "Préstamo no encontrado"},
        409: {"description": "El préstamo no tiene multa o ya fue pagada"},
    },
)
def pagar_multa(
    id: int,
    db: SessionDep,
):
    """Registra el pago de la multa de un préstamo (409 si no tiene multa o ya fue pagada)."""
    return prestamo_controller.pagar_multa(
        db=db,
        prestamo_id=id,
    )
