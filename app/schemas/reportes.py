from datetime import date
from decimal import Decimal
from pydantic import BaseModel, ConfigDict


class LibroMasPrestadoReporte(BaseModel):
    libro_id: int
    titulo: str
    autor: str
    total_prestamos: int

    model_config = ConfigDict(from_attributes=True)


class CategoriaReporte(BaseModel):
    id: int
    nombre: str
    total_libros: int

    model_config = ConfigDict(from_attributes=True)


class PrestamoVencidoReporte(BaseModel):
    prestamo_id: int
    titulo: str
    socio: str
    email: str
    fecha_limite: date
    dias_retraso: int

    model_config = ConfigDict(from_attributes=True)


class SocioConMultasReporte(BaseModel):
    socio_id: int
    nombre: str
    email: str
    total_multas: Decimal
    prestamos_con_multa: int

    model_config = ConfigDict(from_attributes=True)


class AutorReporte(BaseModel):
    autor_id: int
    nombre: str
    total_libros: int
    total_ejemplares: int
    total_prestamos: int

    model_config = ConfigDict(from_attributes=True)


class ResumenReporte(BaseModel):
    total_libros: int
    total_ejemplares: int
    total_prestados: int
    socios_activos: int
    prestamos_vencidos: int
    total_multas: Decimal

    model_config = ConfigDict(from_attributes=True)
