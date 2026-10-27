from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from .core.database import Base, engine
from .core.exceptions import ErrorAplicacion
from .routes.autor import router as autor_router
from .routes.categoria import router as categoria_router
from .routes.libro import router as libro_router
from .routes.prestamo import router as prestamo_router
from .routes.reportes import router as reportes_router
from .routes.socio import router as socio_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Crear las tablas en la base de datos al iniciar
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="API de Gestión de Biblioteca",
    description="API REST construida con FastAPI, SQLAlchemy y PostgreSQL para la gestión de biblioteca.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(ErrorAplicacion)
async def error_aplicacion_handler(request: Request, exc: ErrorAplicacion):
    """Manejador global único para las excepciones propias de la aplicación."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# Registro de todas las rutas de la aplicación
app.include_router(autor_router)
app.include_router(categoria_router)
app.include_router(libro_router)
app.include_router(socio_router)
app.include_router(prestamo_router)
app.include_router(reportes_router)


@app.get("/", tags=["Salud"])
def root():
    return {
        "mensaje": "Bienvenido a la API REST de Gestión de Biblioteca",
        "docs": "/docs",
        "redoc": "/redoc",
    }
