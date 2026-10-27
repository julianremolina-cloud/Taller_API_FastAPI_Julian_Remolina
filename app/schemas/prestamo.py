from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator
from .libro import LibroResponse
from .socio import SocioResponse


class PrestamoCreate(BaseModel):
    libro_id: int = Field(..., description="ID del libro a prestar")
    socio_id: int = Field(..., description="ID del socio que solicita el préstamo")
    fecha_prestamo: Optional[date] = Field(None, description="Fecha del préstamo (por defecto hoy, no puede ser futura)")
    dias: int = Field(14, ge=1, le=30, description="Días de duración del préstamo (1 a 30, por defecto 14)")

    @field_validator("fecha_prestamo")
    @classmethod
    def validar_fecha_no_futura(cls, v: Optional[date]) -> Optional[date]:
        if v is not None and v > date.today():
            raise ValueError("La fecha de préstamo no puede ser futura")
        return v


class DevolucionCreate(BaseModel):
    fecha_devolucion: Optional[date] = Field(None, description="Fecha de devolución (por defecto hoy)")


class PrestamoResponse(BaseModel):
    id: int
    libro_id: int
    socio_id: int
    fecha_prestamo: date
    fecha_limite: date
    fecha_devolucion: Optional[date] = None
    multa: Decimal = Decimal("0.00")
    estado: str

    model_config = ConfigDict(from_attributes=True)


class PrestamoDetalleResponse(PrestamoResponse):
    libro: LibroResponse
    socio: SocioResponse

    model_config = ConfigDict(from_attributes=True)
