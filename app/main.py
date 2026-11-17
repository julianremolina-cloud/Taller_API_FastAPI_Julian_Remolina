from contextlib import asynccontextmanager
import logging
import time
from uuid import uuid4

from fastapi import APIRouter, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .core.config import get_settings
from .core.exceptions import ErrorAplicacion
from .core.limiter import limiter
from .routes.auth import router as auth_router
from .routes.autor import router as autor_router
from .routes.categoria import router as categoria_router
from .routes.health import router as health_router
from .routes.libro import router as libro_router
from .routes.prestamo import router as prestamo_router
from .routes.reportes import router as reportes_router
from .routes.socio import router as socio_router
from .routes.usuario import router as usuario_router

settings = get_settings()

logger = logging.getLogger("biblioteca.api")
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

# Validación CORS para producción
if settings.environment == "prod" and "*" in settings.cors_origins:
    raise ValueError("No se permite el origen comodín '*' en producción")

docs_url = "/docs" if settings.environment != "prod" else None
redoc_url = "/redoc" if settings.environment != "prod" else None


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="API de Gestión de Biblioteca",
    description="API REST segura construida con FastAPI, SQLAlchemy, Alembic y PostgreSQL.",
    version="2.0.0",
    lifespan=lifespan,
    docs_url=docs_url,
    redoc_url=redoc_url,
)

# Estado de rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Middleware de Request ID y auditoría de peticiones
@app.middleware("http")
async def request_id_and_logging_middleware(request: Request, call_next):
    request_id = str(uuid4())
    start_time = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000

    response.headers["X-Request-ID"] = request_id
    logger.info(
        f"request_id={request_id} method={request.method} path={request.url.path} "
        f"status={response.status_code} duration={duration_ms:.2f}ms"
    )
    return response


# Manejador de excepciones propias de la aplicación
@app.exception_handler(ErrorAplicacion)
async def error_aplicacion_handler(request: Request, exc: ErrorAplicacion):
    """Manejador global para las excepciones de negocio y autenticación."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=exc.headers,
    )


# Manejador controlado para errores 500 no capturados
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Captura cualquier excepción imprevista sin exponer el stacktrace."""
    logger.error(f"Error no controlado en la solicitud: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Error interno del servidor"},
    )


# Router principal unificado con prefijo /api/v1
api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(autor_router)
api_v1_router.include_router(categoria_router)
api_v1_router.include_router(libro_router)
api_v1_router.include_router(socio_router)
api_v1_router.include_router(prestamo_router)
api_v1_router.include_router(reportes_router)
api_v1_router.include_router(usuario_router)

app.include_router(api_v1_router)


@app.get("/", tags=["Salud"])
def root():
    return {
        "mensaje": "Bienvenido a la API REST de Gestión de Biblioteca v2",
        "version": "2.0.0",
        "docs": docs_url,
        "redoc": redoc_url,
    }
