from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from ..core.database import Base


class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nombre = Column(String(50), unique=True, nullable=False, index=True)
    descripcion = Column(String(200), nullable=True)

    libros = relationship("Libro", secondary="libro_categoria", back_populates="categorias")
