import getpass
import sys
from sqlalchemy import select
from app.core.database import SessionLocal
from app.core.security import hashear_password
from app.models.usuario import RolUsuario, Usuario


def crear_admin():
    print("=== Creación del Administrador del Sistema ===")
    try:
        email = input("Email: ").strip().lower()
        nombre = input("Nombre: ").strip().title()
        password = getpass.getpass("Contraseña: ")
    except (EOFError, KeyboardInterrupt):
        print("\nOperación cancelada.")
        return

    if not email or not nombre or not password:
        print("Error: Todos los campos son obligatorios.")
        sys.exit(1)

    db = SessionLocal()
    try:
        usuario_existente = db.scalar(select(Usuario).where(Usuario.email == email))
        if usuario_existente:
            print(f"El usuario con email '{email}' ya existe. No se realizaron cambios.")
            return

        admin = Usuario(
            email=email,
            nombre=nombre,
            password_hash=hashear_password(password),
            rol=RolUsuario.admin,
            activo=True,
            intentos_fallidos=0,
            bloqueado_hasta=None,
            socio_id=None,
        )
        db.add(admin)
        db.commit()
        print(f"Administrador '{email}' creado exitosamente.")
    finally:
        db.close()


if __name__ == "__main__":
    crear_admin()
