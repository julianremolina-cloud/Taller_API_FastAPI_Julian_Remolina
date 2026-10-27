class ErrorAplicacion(Exception):
    """Clase base de todas las excepciones propias de la aplicación."""
    status_code: int = 400

    def __init__(self, detail: str = "Error en la aplicación"):
        self.detail = detail
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
