from fastapi import APIRouter, Query

from ..controllers import reportes as reportes_controller
from ..core.dependencies import SessionDep, requiere_rol
from ..models.usuario import RolUsuario
from ..schemas.reportes import (
    AutorReporte,
    CategoriaReporte,
    LibroMasPrestadoReporte,
    PrestamoVencidoReporte,
    ResumenReporte,
    SocioConMultasReporte,
)

router = APIRouter(
    prefix="/reportes",
    tags=["Reportes"],
    dependencies=[requiere_rol(RolUsuario.admin, RolUsuario.bibliotecario)],
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Permisos insuficientes (solo staff)"},
    },
)


@router.get("/libros-mas-prestados", response_model=list[LibroMasPrestadoReporte])
def obtener_libros_mas_prestados(
    db: SessionDep,
    limite: int = Query(5, ge=1, le=100, description="Cantidad máxima de libros a retornar"),
):
    """Retorna los libros más prestados ordenados de mayor a menor."""
    return reportes_controller.reporte_libros_mas_prestados(db=db, limite=limite)


@router.get("/categorias", response_model=list[CategoriaReporte])
def obtener_reporte_categorias(db: SessionDep):
    """Retorna el total de libros por categoría, incluidas las que tienen 0."""
    return reportes_controller.reporte_categorias(db=db)


@router.get("/prestamos-vencidos", response_model=list[PrestamoVencidoReporte])
def obtener_prestamos_vencidos(db: SessionDep):
    """Retorna los préstamos actualmente vencidos con días de retraso."""
    return reportes_controller.reporte_prestamos_vencidos(db=db)


@router.get("/socios-con-multas", response_model=list[SocioConMultasReporte])
def obtener_socios_con_multas(db: SessionDep):
    """Retorna los socios con multas acumuladas mayores a cero."""
    return reportes_controller.reporte_socios_con_multas(db=db)


@router.get("/autores", response_model=list[AutorReporte])
def obtener_reporte_autores(db: SessionDep):
    """Retorna libros, ejemplares y préstamos de cada autor."""
    return reportes_controller.reporte_autores(db=db)


@router.get("/resumen", response_model=ResumenReporte)
def obtener_reporte_resumen(db: SessionDep):
    """Retorna métricas globales consolidadas del sistema de biblioteca."""
    return reportes_controller.reporte_resumen(db=db)
