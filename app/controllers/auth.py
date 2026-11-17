from datetime import datetime, timedelta, timezone
from fastapi.security import OAuth2PasswordRequestForm
import jwt
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import (
    Conflicto,
    CuentaBloqueada,
    NoAutenticado,
    Prohibido,
    ReglaNegocio,
)
from app.core.security import crear_token, hashear_password, verificar_password
from app.models.refresh_token import RefreshToken
from app.models.socio import Socio
from app.models.usuario import RolUsuario, Usuario
from app.schemas.auth import PasswordCambiar, TokenRespuesta
from app.schemas.usuario import UsuarioRegistro

settings = get_settings()


def registrar_socio(db: Session, datos: UsuarioRegistro) -> Usuario:
    """
    Crea un usuario con rol socio y su correspondiente registro en la tabla socios
    dentro de una única transacción atómica. Si el email ya existe en cualquiera
    de las dos tablas, lanza Conflicto (HTTP 409).
    """
    email_normalizado = datos.email.lower()

    # Validar unicidad en usuarios
    usuario_existente = db.scalar(select(Usuario).where(Usuario.email == email_normalizado))
    if usuario_existente:
        raise Conflicto("El correo electrónico ya está registrado")

    # Validar unicidad en socios
    socio_existente = db.scalar(select(Socio).where(Socio.email == email_normalizado))
    if socio_existente:
        raise Conflicto("El correo electrónico ya está registrado en socios")

    # Crear socio
    nuevo_socio = Socio(
        nombre=datos.nombre,
        email=email_normalizado,
        telefono=datos.telefono,
        activo=True,
    )
    db.add(nuevo_socio)
    db.flush()

    # Crear usuario vinculado
    nuevo_usuario = Usuario(
        email=email_normalizado,
        nombre=datos.nombre,
        password_hash=hashear_password(datos.password),
        rol=RolUsuario.socio,
        activo=True,
        intentos_fallidos=0,
        bloqueado_hasta=None,
        socio_id=nuevo_socio.id,
    )
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)
    return nuevo_usuario


def iniciar_sesion(db: Session, form_data: OAuth2PasswordRequestForm) -> TokenRespuesta:
    """
    Autenticación con OAuth2 Password Flow.
    Aplica las reglas A1 (credenciales válidas), A2 (activo), y A3 (bloqueo tras 5 fallos).
    """
    email = form_data.username.strip().lower()
    password = form_data.password
    ahora = datetime.now(timezone.utc)

    usuario = db.scalar(select(Usuario).where(Usuario.email == email))

    # Regla A3: Verificar si la cuenta está bloqueada temporalmente
    if usuario and usuario.bloqueado_hasta is not None:
        if usuario.bloqueado_hasta > ahora:
            raise CuentaBloqueada("Cuenta bloqueada temporalmente")
        else:
            # Si el bloqueo ya expiró, restablecer
            usuario.bloqueado_hasta = None
            usuario.intentos_fallidos = 0
            db.commit()

    # Regla A1: Mismo mensaje si el usuario no existe o contraseña incorrecta
    if not usuario:
        raise NoAutenticado("Credenciales inválidas")

    if not verificar_password(password, usuario.password_hash):
        usuario.intentos_fallidos += 1
        if usuario.intentos_fallidos >= 5:
            usuario.bloqueado_hasta = ahora + timedelta(minutes=15)
            db.commit()
            raise CuentaBloqueada("Cuenta bloqueada temporalmente")
        db.commit()
        raise NoAutenticado("Credenciales inválidas")

    # Regla A2: Verificar si está activo
    if not usuario.activo:
        raise Prohibido("Usuario inactivo")

    # Login exitoso: reiniciar intentos fallidos
    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None

    access_dur = timedelta(minutes=settings.access_token_expire_minutes)
    refresh_dur = timedelta(days=settings.refresh_token_expire_days)

    access_token, _ = crear_token(usuario.id, usuario.rol.value, "access", access_dur)
    refresh_token, refresh_jti = crear_token(usuario.id, usuario.rol.value, "refresh", refresh_dur)

    # Registrar el refresh token en la base de datos
    nuevo_rt = RefreshToken(
        jti=refresh_jti,
        usuario_id=usuario.id,
        expira_en=ahora + refresh_dur,
        revocado=False,
    )
    db.add(nuevo_rt)
    db.commit()

    return TokenRespuesta(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=int(access_dur.total_seconds()),
    )


def refrescar_token(db: Session, refresh_token_str: str) -> TokenRespuesta:
    """
    Rotación de refresh tokens: revoca el token usado y entrega un nuevo par.
    Regla A5 (claim type) y A6 (no revocado/vencido; revocación masiva ante reuso).
    """
    try:
        payload = jwt.decode(refresh_token_str, settings.secret_key, algorithms=[settings.algorithm])
    except jwt.InvalidTokenError:
        raise NoAutenticado("Token inválido o vencido")

    if payload.get("type") != "refresh":
        raise NoAutenticado("Tipo de token inválido")

    jti = payload.get("jti")
    if not jti:
        raise NoAutenticado("Token inválido")

    token_record = db.scalar(select(RefreshToken).where(RefreshToken.jti == jti))
    if not token_record:
        raise NoAutenticado("Refresh token no encontrado")

    # Regla A6: Si se reutiliza uno ya revocado/rotado, se revocan todos los refresh tokens
    if token_record.revocado:
        db.execute(
            update(RefreshToken)
            .where(RefreshToken.usuario_id == token_record.usuario_id)
            .values(revocado=True)
        )
        db.commit()
        raise NoAutenticado("Token ya utilizado o revocado")

    ahora = datetime.now(timezone.utc)
    if token_record.expira_en < ahora:
        token_record.revocado = True
        db.commit()
        raise NoAutenticado("Refresh token vencido")

    usuario = db.get(Usuario, token_record.usuario_id)
    if not usuario:
        raise NoAutenticado("Usuario no encontrado")
    if not usuario.activo:
        raise Prohibido("Usuario inactivo")

    # Revocar el refresh token actual
    token_record.revocado = True

    access_dur = timedelta(minutes=settings.access_token_expire_minutes)
    refresh_dur = timedelta(days=settings.refresh_token_expire_days)

    new_access_token, _ = crear_token(usuario.id, usuario.rol.value, "access", access_dur)
    new_refresh_token, new_jti = crear_token(usuario.id, usuario.rol.value, "refresh", refresh_dur)

    nuevo_rt = RefreshToken(
        jti=new_jti,
        usuario_id=usuario.id,
        expira_en=ahora + refresh_dur,
        revocado=False,
    )
    db.add(nuevo_rt)
    db.commit()

    return TokenRespuesta(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        token_type="bearer",
        expires_in=int(access_dur.total_seconds()),
    )


def cerrar_sesion(db: Session, refresh_token_str: str) -> None:
    """Revoca el refresh token especificado."""
    try:
        payload = jwt.decode(refresh_token_str, settings.secret_key, algorithms=[settings.algorithm])
        jti = payload.get("jti")
        if jti:
            token_record = db.scalar(select(RefreshToken).where(RefreshToken.jti == jti))
            if token_record:
                token_record.revocado = True
                db.commit()
    except jwt.InvalidTokenError:
        raise NoAutenticado("Token inválido o vencido")


def cambiar_password(db: Session, usuario: Usuario, datos: PasswordCambiar) -> None:
    """Cambia la contraseña del usuario y revoca todos sus refresh tokens."""
    if not verificar_password(datos.password_actual, usuario.password_hash):
        raise ReglaNegocio("La contraseña actual es incorrecta")

    usuario.password_hash = hashear_password(datos.password_nueva)
    # Revocar todos los refresh tokens
    db.execute(
        update(RefreshToken)
        .where(RefreshToken.usuario_id == usuario.id)
        .values(revocado=True)
    )
    db.commit()
