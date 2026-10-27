"""
Script para inicializar la base de datos con los datos de prueba del taller.
Ejecución: python seed.py
"""
import os
from dotenv import load_dotenv
import sqlalchemy
from app.core.database import Base, SessionLocal, engine
from app.models.autor import Autor
from app.models.categoria import Categoria
from app.models.libro import Libro
from app.models.socio import Socio

load_dotenv()


def sembrar_datos():
    print("Creando tablas si no existen...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Limpiar datos existentes en cascada
        print("Limpiando tablas existentes...")
        with engine.connect() as conn:
            conn.execute(
                sqlalchemy.text(
                    "TRUNCATE prestamos, libro_categoria, libros, categorias, socios, autores RESTART IDENTITY CASCADE;"
                )
            )
            conn.commit()

        print("Insertando autores...")
        autor1 = Autor(nombre="Gabriel García Márquez", nacionalidad="Colombiana", anio_nacimiento=1927)
        autor2 = Autor(nombre="Isabel Allende", nacionalidad="Chilena", anio_nacimiento=1942)
        autor3 = Autor(nombre="George Orwell", nacionalidad="Británica", anio_nacimiento=1903)
        db.add_all([autor1, autor2, autor3])
        db.commit()

        print("Insertando categorías...")
        cat1 = Categoria(nombre="novela", descripcion="Obras narrativas de ficción")
        cat2 = Categoria(nombre="realismo mágico", descripcion="Elementos mágicos en un entorno realista")
        cat3 = Categoria(nombre="distopía", descripcion="Sociedades ficticias indeseables")
        cat4 = Categoria(nombre="poesía", descripcion="Composiciones literarias poéticas")
        db.add_all([cat1, cat2, cat3, cat4])
        db.commit()

        print("Insertando libros...")
        libro1 = Libro(
            titulo="Cien Años De Soledad",
            isbn="9780307474728",
            anio_publicacion=1967,
            ejemplares=2,
            autor_id=autor1.id,
        )
        libro1.categorias = [cat1, cat2]

        libro2 = Libro(
            titulo="El Amor En Los Tiempos Del Cólera",
            isbn="9780307389732",
            anio_publicacion=1985,
            ejemplares=1,
            autor_id=autor1.id,
        )
        libro2.categorias = [cat1]

        libro3 = Libro(
            titulo="La Casa De Los Espíritus",
            isbn="9788401341991",
            anio_publicacion=1982,
            ejemplares=2,
            autor_id=autor2.id,
        )
        libro3.categorias = [cat1, cat2]

        libro4 = Libro(
            titulo="1984",
            isbn="9780451524935",
            anio_publicacion=1949,
            ejemplares=3,
            autor_id=autor3.id,
        )
        libro4.categorias = [cat1, cat3]

        db.add_all([libro1, libro2, libro3, libro4])
        db.commit()

        print("Insertando socios...")
        socio1 = Socio(nombre="Ana Torres", email="ana@example.com", activo=True)
        socio2 = Socio(nombre="Luis Pérez", email="luis@example.com", activo=True)
        socio3 = Socio(nombre="Marta Ruiz", email="marta@example.com", activo=True)
        db.add_all([socio1, socio2, socio3])
        db.commit()

        print("¡Base de datos inicializada exitosamente con todos los datos de prueba!")
    finally:
        db.close()


if __name__ == "__main__":
    sembrar_datos()
