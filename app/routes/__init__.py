from .autor import router as autor_router
from .categoria import router as categoria_router
from .libro import router as libro_router
from .socio import router as socio_router
from .prestamo import router as prestamo_router
from .reportes import router as reportes_router

__all__ = [
    "autor_router",
    "categoria_router",
    "libro_router",
    "socio_router",
    "prestamo_router",
    "reportes_router",
]
