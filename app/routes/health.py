from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.dependencies import SessionDep

router = APIRouter(prefix="/health", tags=["Salud"])


@router.get(
    "",
    summary="Estado de salud de la API y de la base de datos",
    responses={
        200: {
            "description": "Servicio funcionando normalmente",
            "content": {"application/json": {"example": {"status": "ok", "database": "ok"}}},
        },
        503: {
            "description": "La base de datos no responde",
            "content": {"application/json": {"example": {"status": "error", "database": "error"}}},
        },
    },
)
def verificar_salud(db: SessionDep):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "ok"}
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "error", "database": "error"},
        )
