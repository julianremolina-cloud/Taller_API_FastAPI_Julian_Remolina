from sqlalchemy import Column, ForeignKey, Integer, String, Table
from sqlalchemy.orm import relationship
from ..core.database import Base

libro_categoria = Table(
    "libro_categoria",
    Base.metadata,
    Column("libro_id", Integer, ForeignKey("libros.id", ondelete="CASCADE"), primary_key=True),
    Column("categoria_id", Integer, ForeignKey("categorias.id", ondelete="CASCADE"), primary_key=True),
)


class Libro(Base):
    __tablename__ = "libros"

    id = Column(Integer, primary_key=True, index=True)
    titulo = Column(String(150), nullable=False, index=True)
    isbn = Column(String(13), unique=True, nullable=False, index=True)
    anio_publicacion = Column(Integer, nullable=False)
    ejemplares = Column(Integer, nullable=False)
    autor_id = Column(Integer, ForeignKey("autores.id"), nullable=False)

    autor = relationship("Autor", back_populates="libros")
    categorias = relationship("Categoria", secondary=libro_categoria, back_populates="libros")
    prestamos = relationship("Prestamo", back_populates="libro")
