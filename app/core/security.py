from datetime import datetime, timedelta, timezone
from uuid import uuid4
import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

settings = get_settings()
password_hash = PasswordHash.recommended()  # Argon2


def hashear_password(password: str) -> str:
    """Genera hash seguro Argon2 a partir de la contraseña plana."""
    return password_hash.hash(password)


def verificar_password(password: str, hash_guardado: str) -> bool:
    """Verifica si la contraseña coincide con el hash almacenado."""
    return password_hash.verify(password, hash_guardado)


def crear_token(usuario_id: int, rol: str, tipo: str, duracion: timedelta) -> tuple[str, str]:
    """
    Crea un JSON Web Token (JWT) firmado con algoritmo HS256 y claims estándar.
    Retorna la tupla (token_str, jti).
    """
    ahora = datetime.now(timezone.utc)
    jti = str(uuid4())
    payload = {
        "sub": str(usuario_id),
        "rol": rol,
        "type": tipo,
        "iat": ahora,
        "exp": ahora + duracion,
        "jti": jti,
    }
    token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
    return token, jti
