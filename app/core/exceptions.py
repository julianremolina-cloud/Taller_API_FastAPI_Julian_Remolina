class ErrorAplicacion(Exception):
    """Clase base de todas las excepciones propias de la aplicación."""
    status_code: int = 400
    headers: dict[str, str] | None = None

    def __init__(self, detail: str = "Error en la aplicación", headers: dict[str, str] | None = None):
        self.detail = detail
        self.headers = headers
        super().__init__(detail)


class NoEncontrado(ErrorAplicacion):
    """El recurso solicitado no existe (HTTP 404)."""
    status_code: int = 404

    def __init__(self, detail: str = "Recurso no encontrado"):
        super().__init__(detail)


class Conflicto(ErrorAplicacion):
    """Datos duplicados o intento de borrar un registro con dependencias (HTTP 409)."""
    status_code: int = 409

    def __init__(self, detail: str = "Conflicto con los datos del recurso"):
        super().__init__(detail)


class ReglaNegocio(ErrorAplicacion):
    """Una regla del negocio de la biblioteca no se cumple (HTTP 422)."""
    status_code: int = 422

    def __init__(self, detail: str = "Regla de negocio no cumplida"):
        super().__init__(detail)


class NoAutenticado(ErrorAplicacion):
    """Falta el token, es inválido, venció o credenciales erróneas (HTTP 401)."""
    status_code: int = 401

    def __init__(self, detail: str = "No autenticado"):
        super().__init__(detail, headers={"WWW-Authenticate": "Bearer"})


class Prohibido(ErrorAplicacion):
    """El usuario está autenticado pero no tiene permiso (HTTP 403)."""
    status_code: int = 403

    def __init__(self, detail: str = "No tiene permisos para esta acción"):
        super().__init__(detail)


class CuentaBloqueada(ErrorAplicacion):
    """Demasiados intentos fallidos de inicio de sesión (HTTP 423)."""
    status_code: int = 423

    def __init__(self, detail: str = "Cuenta bloqueada temporalmente"):
        super().__init__(detail)
