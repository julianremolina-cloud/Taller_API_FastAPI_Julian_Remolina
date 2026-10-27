from datetime import date
from sqlalchemy import Column, Date, ForeignKey, Integer, Numeric
from sqlalchemy.orm import relationship
from ..core.database import Base


class Prestamo(Base):
    __tablename__ = "prestamos"

    id = Column(Integer, primary_key=True, index=True)
    libro_id = Column(Integer, ForeignKey("libros.id"), nullable=False)
    socio_id = Column(Integer, ForeignKey("socios.id"), nullable=False)
    fecha_prestamo = Column(Date, default=date.today, nullable=False)
    fecha_limite = Column(Date, nullable=False)
    fecha_devolucion = Column(Date, nullable=True)
    multa = Column(Numeric(10, 2), default=0.0, nullable=False)

    libro = relationship("Libro", back_populates="prestamos")
    socio = relationship("Socio", back_populates="prestamos")

    @property
    def estado(self) -> str:
        if self.fecha_devolucion is not None:
            return "devuelto"
        if self.fecha_limite < date.today():
            return "vencido"
        return "activo"
