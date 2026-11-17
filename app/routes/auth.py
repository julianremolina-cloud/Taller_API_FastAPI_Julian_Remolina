from typing import Annotated
from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app.controllers import auth as auth_controller
from app.core.dependencies import CurrentUser, SessionDep
from app.core.limiter import limiter
from app.schemas.auth import PasswordCambiar, RefreshTokenSolicitud, TokenRespuesta
from app.schemas.usuario import UsuarioRegistro, UsuarioRespuesta

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post(
    "/registro",
    response_model=UsuarioRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Registro público de socios",
    responses={
        201: {"description": "Usuario y socio creados exitosamente"},
        409: {"description": "El correo ya está registrado"},
        422: {"description": "Error de validación en los datos ingresados"},
        429: {"description": "Límite de peticiones excedido (máximo 5/minuto)"},
    },
)
@limiter.limit("5/minute")
def registro_socio(
    request: Request,
    datos: UsuarioRegistro,
    db: SessionDep,
):
    """Crea una cuenta de usuario con rol socio y su ficha de socio asociada en una única transacción."""
    return auth_controller.registrar_socio(db=db, datos=datos)


@router.post(
    "/login",
    response_model=TokenRespuesta,
    summary="Inicio de sesión con credenciales OAuth2",
    responses={
        200: {"description": "Inicio de sesión exitoso"},
        401: {"description": "Credenciales inválidas"},
        403: {"description": "Usuario inactivo"},
        423: {"description": "Cuenta bloqueada temporalmente"},
        429: {"description": "Límite de peticiones excedido (máximo 10/minuto)"},
    },
)
@limiter.limit("10/minute")
def login(
    request: Request,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: SessionDep,
):
    """Valida usuario y contraseña, entregando access token y refresh token."""
    return auth_controller.iniciar_sesion(db=db, form_data=form_data)


@router.post(
    "/refresh",
    response_model=TokenRespuesta,
    summary="Rotación y renovación de tokens",
    responses={
        200: {"description": "Tokens renovados exitosamente"},
        401: {"description": "Token inválido, vencido o ya revocado"},
        403: {"description": "Usuario inactivo"},
    },
)
def refrescar(datos: RefreshTokenSolicitud, db: SessionDep):
    """Revoca el refresh token actual y genera un nuevo par de tokens (rotación)."""
    return auth_controller.refrescar_token(db=db, refresh_token_str=datos.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cierre de sesión",
    responses={
        204: {"description": "Sesión cerrada y refresh token revocado"},
        401: {"description": "Token inválido"},
    },
)
def logout(datos: RefreshTokenSolicitud, db: SessionDep):
    """Revoca el refresh token para cerrar la sesión."""
    auth_controller.cerrar_sesion(db=db, refresh_token_str=datos.refresh_token)


@router.get(
    "/me",
    response_model=UsuarioRespuesta,
    summary="Información del usuario autenticado",
    responses={
        200: {"description": "Datos del perfil autenticado"},
        401: {"description": "Token ausente o inválido"},
        403: {"description": "Usuario inactivo"},
    },
)
def obtener_perfil_actual(usuario: CurrentUser):
    """Retorna los datos del usuario correspondiente al token de acceso proporcionado."""
    return usuario


@router.patch(
    "/me/password",
    status_code=status.HTTP_200_OK,
    summary="Cambio de contraseña del usuario autenticado",
    responses={
        200: {"description": "Contraseña actualizada exitosamente"},
        401: {"description": "No autenticado"},
        422: {"description": "Contraseña actual incorrecta o formato inválido"},
    },
)
def cambiar_password(
    datos: PasswordCambiar,
    usuario: CurrentUser,
    db: SessionDep,
):
    """Permite al usuario autenticado cambiar su contraseña, revocando todos sus refresh tokens."""
    auth_controller.cambiar_password(db=db, usuario=usuario, datos=datos)
    return {"detail": "Contraseña actualizada exitosamente"}
