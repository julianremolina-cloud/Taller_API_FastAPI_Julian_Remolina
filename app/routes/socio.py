from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, status

from ..controllers import prestamo as prestamo_controller
from ..controllers import socio as socio_controller
from ..core.dependencies import CurrentUser, PaginacionDep, SessionDep, requiere_rol
from ..models.usuario import RolUsuario
from ..schemas.pagina import Pagina
from ..schemas.prestamo import PrestamoResponse
from ..schemas.socio import SocioCreate, SocioResponse, SocioUpdate
from ..schemas.usuario import SocioActualizarPropio

router = APIRouter(prefix="/socios", tags=["Socios"])


# --- Endpoints propios del socio (/socios/me) ---
@router.get(
    "/me",
    response_model=SocioResponse,
    dependencies=[requiere_rol(RolUsuario.socio)],
    summary="Consultar el perfil propio del socio",
    responses={
        200: {"description": "Ficha del socio autenticado"},
        401: {"description": "No autenticado"},
        403: {"description": "Solo accesible para socios"},
    },
)
def obtener_mi_perfil(usuario: CurrentUser, db: SessionDep):
    """Retorna los datos de socio vinculados al usuario autenticado."""
    return socio_controller.obtener_perfil_socio(db=db, usuario=usuario)


@router.patch(
    "/me",
    response_model=SocioResponse,
    dependencies=[requiere_rol(RolUsuario.socio)],
    summary="Actualizar perfil propio del socio",
    responses={
        200: {"description": "Perfil actualizado"},
        401: {"description": "No autenticado"},
        403: {"description": "Solo accesible para socios"},
        422: {"description": "Error si se intentan modificar campos no permitidos (extra=forbid)"},
    },
)
def actualizar_mi_perfil(
    datos: SocioActualizarPropio,
    usuario: CurrentUser,
    db: SessionDep,
):
    """Actualiza únicamente nombre y/o teléfono del socio propio (regla Z4)."""
    return socio_controller.actualizar_perfil_socio(db=db, usuario=usuario, datos=datos)


@router.get(
    "/me/prestamos",
    response_model=Pagina[PrestamoResponse],
    dependencies=[requiere_rol(RolUsuario.socio)],
    summary="Consultar préstamos propios",
    responses={
        200: {"description": "Listado de préstamos propios"},
        401: {"description": "No autenticado"},
        403: {"description": "Solo accesible para socios"},
    },
)
def listar_mis_prestamos(
    db: SessionDep,
    pag: PaginacionDep,
    usuario: CurrentUser,
    estado: Optional[str] = Query(None, description="Filtrar por estado: activo, vencido, devuelto"),
):
    """Retorna la lista paginada de préstamos pertenecientes al socio autenticado."""
    return prestamo_controller.listar_prestamos(
        db=db,
        skip=pag.skip,
        limit=pag.limit,
        usuario=usuario,
        estado=estado,
    )


@router.get(
    "/me/multas",
    dependencies=[requiere_rol(RolUsuario.socio)],
    summary="Consultar multas pendientes propias",
    responses={
        200: {"description": "Detalle de multas pendientes y total adeudado"},
        401: {"description": "No autenticado"},
        403: {"description": "Solo accesible para socios"},
    },
)
def obtener_mis_multas(usuario: CurrentUser, db: SessionDep):
    """Retorna la lista de préstamos con multas no pagadas y el total adeudado."""
    return socio_controller.obtener_multas_propias(db=db, usuario=usuario)


# --- Endpoints administrativos de socios ---
@router.get(
    "",
    response_model=Pagina[SocioResponse],
    dependencies=[requiere_rol(RolUsuario.admin, RolUsuario.bibliotecario)],
    summary="Listado paginado de socios",
    responses={
        200: {"description": "Listado de socios con total"},
        401: {"description": "No autenticado"},
        403: {"description": "Solo staff (bibliotecario o admin)"},
    },
)
def listar_socios(
    db: SessionDep,
    pag: PaginacionDep,
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo"),
):
    """Lista socios paginados con filtro opcional por estado."""
    return socio_controller.listar_socios(
        db=db,
        skip=pag.skip,
        limit=pag.limit,
        activo=activo,
    )


@router.get(
    "/{id}",
    response_model=SocioResponse,
    dependencies=[requiere_rol(RolUsuario.admin, RolUsuario.bibliotecario)],
    summary="Consulta detalle de un socio",
    responses={
        200: {"description": "Detalle del socio"},
        401: {"description": "No autenticado"},
        403: {"description": "Solo staff"},
        404: {"description": "Socio no encontrado"},
    },
)
def obtener_socio(id: int, db: SessionDep):
    """Consulta un socio por su ID."""
    return socio_controller.obtener_socio_por_id(db=db, socio_id=id)


@router.post(
    "",
    response_model=SocioResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[requiere_rol(RolUsuario.admin, RolUsuario.bibliotecario)],
    summary="Crear un nuevo socio manualmente",
    responses={
        201: {"description": "Socio creado exitosamente"},
        401: {"description": "No autenticado"},
        403: {"description": "Solo staff"},
        409: {"description": "Email ya registrado"},
    },
)
def crear_socio(socio_in: SocioCreate, db: SessionDep):
    """Crea un nuevo socio en el sistema."""
    return socio_controller.crear_socio(db=db, socio_in=socio_in)


@router.patch(
    "/{id}",
    response_model=SocioResponse,
    dependencies=[requiere_rol(RolUsuario.admin, RolUsuario.bibliotecario)],
    summary="Actualizar un socio",
    responses={
        200: {"description": "Socio actualizado"},
        401: {"description": "No autenticado"},
        403: {"description": "Solo staff"},
        404: {"description": "Socio no encontrado"},
        409: {"description": "Email ya registrado por otro socio"},
    },
)
def actualizar_socio(
    id: int,
    socio_in: SocioUpdate,
    db: SessionDep,
):
    """Actualiza los datos de un socio."""
    return socio_controller.actualizar_socio(db=db, socio_id=id, socio_in=socio_in)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[requiere_rol(RolUsuario.admin)],
    summary="Eliminar un socio",
    responses={
        204: {"description": "Socio eliminado"},
        401: {"description": "No autenticado"},
        403: {"description": "Solo administrador"},
        404: {"description": "Socio no encontrado"},
        409: {"description": "No se puede eliminar porque tiene préstamos activos"},
    },
)
def eliminar_socio(id: int, db: SessionDep):
    """Elimina un socio si no tiene préstamos activos."""
    socio_controller.eliminar_socio(db=db, socio_id=id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
