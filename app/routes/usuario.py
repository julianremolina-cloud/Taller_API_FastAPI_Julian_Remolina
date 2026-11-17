from typing import Optional
from fastapi import APIRouter, Query, status

from app.controllers import usuario as usuario_controller
from app.core.dependencies import CurrentUser, PaginacionDep, SessionDep, requiere_rol
from app.models.usuario import RolUsuario
from app.schemas.pagina import Pagina
from app.schemas.usuario import (
    UsuarioActivoActualizar,
    UsuarioCrear,
    UsuarioRespuesta,
    UsuarioRolActualizar,
)

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"],
    dependencies=[requiere_rol(RolUsuario.admin)],
    responses={
        401: {"description": "No autenticado"},
        403: {"description": "Acceso exclusivo para administradores"},
    },
)


@router.get(
    "",
    response_model=Pagina[UsuarioRespuesta],
    summary="Listado paginado de usuarios",
    responses={200: {"description": "Listado de usuarios con total"}},
)
def listar_usuarios(
    db: SessionDep,
    pag: PaginacionDep,
    rol: Optional[RolUsuario] = Query(None, description="Filtrar por rol"),
    activo: Optional[bool] = Query(None, description="Filtrar por estado activo"),
):
    """Lista usuarios del sistema con filtros opcionales."""
    return usuario_controller.listar_usuarios(
        db=db,
        skip=pag.skip,
        limit=pag.limit,
        rol=rol,
        activo=activo,
    )


@router.post(
    "",
    response_model=UsuarioRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Crear usuario bibliotecario o administrador",
    responses={
        201: {"description": "Usuario staff creado exitosamente"},
        409: {"description": "Correo ya registrado"},
        422: {"description": "Rol no permitido o validación fallida"},
    },
)
def crear_usuario(datos: UsuarioCrear, db: SessionDep):
    """Crea una cuenta para personal administrativo (bibliotecario o admin)."""
    return usuario_controller.crear_usuario_staff(db=db, datos=datos)


@router.patch(
    "/{id}/rol",
    response_model=UsuarioRespuesta,
    summary="Cambiar el rol de un usuario",
    responses={
        200: {"description": "Rol modificado exitosamente"},
        404: {"description": "Usuario no encontrado"},
        422: {"description": "Un admin no puede quitarse el rol a sí mismo (regla Z5)"},
    },
)
def cambiar_rol(
    id: int,
    datos: UsuarioRolActualizar,
    db: SessionDep,
    usuario_actual: CurrentUser,
):
    """Actualiza el rol de un usuario y revoca sus refresh tokens (regla Z6)."""
    return usuario_controller.cambiar_rol_usuario(
        db=db,
        usuario_id=id,
        nuevo_rol=datos.rol,
        admin_actual=usuario_actual,
    )


@router.patch(
    "/{id}/activo",
    response_model=UsuarioRespuesta,
    summary="Activar o desactivar una cuenta de usuario",
    responses={
        200: {"description": "Estado activo actualizado exitosamente"},
        404: {"description": "Usuario no encontrado"},
        422: {"description": "Un admin no puede desactivarse a sí mismo (regla Z5)"},
    },
)
def cambiar_activo(
    id: int,
    datos: UsuarioActivoActualizar,
    db: SessionDep,
    usuario_actual: CurrentUser,
):
    """Activa o desactiva a un usuario y revoca sus refresh tokens (regla Z6)."""
    return usuario_controller.cambiar_activo_usuario(
        db=db,
        usuario_id=id,
        activo=datos.activo,
        admin_actual=usuario_actual,
    )
