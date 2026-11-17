from datetime import date, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.core.limiter import limiter
from app.core.security import crear_token, hashear_password, verificar_password
from app.models.usuario import RolUsuario, Usuario
from tests.conftest import TestingSessionLocal


@pytest.fixture(scope="session")
def auth_tokens(client: TestClient):
    limiter.reset()
    db = TestingSessionLocal()
    # Limpiar y preparar usuarios
    admin = db.scalar(select(Usuario).where(Usuario.email == "admin_cob@biblioteca.com"))
    if not admin:
        admin = Usuario(
            email="admin_cob@biblioteca.com",
            nombre="Admin Cobertura",
            password_hash=hashear_password("Admin1234"),
            rol=RolUsuario.admin,
            activo=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

    # Login admin
    r_adm = client.post("/api/v1/auth/login", data={"username": "admin_cob@biblioteca.com", "password": "Admin1234"})
    adm_token = r_adm.json()["access_token"]
    adm_headers = {"Authorization": f"Bearer {adm_token}"}

    # Crear bibliotecario
    r_bib = client.post(
        "/api/v1/usuarios",
        json={"nombre": "Biblio Cob", "email": "biblio_cob@biblioteca.com", "password": "Biblio1234", "rol": "bibliotecario"},
        headers=adm_headers,
    )
    if r_bib.status_code == 201:
        bib_id = r_bib.json()["id"]
    else:
        bib_u = db.scalar(select(Usuario).where(Usuario.email == "biblio_cob@biblioteca.com"))
        bib_id = bib_u.id

    r_bib_log = client.post("/api/v1/auth/login", data={"username": "biblio_cob@biblioteca.com", "password": "Biblio1234"})
    bib_token = r_bib_log.json()["access_token"]
    bib_headers = {"Authorization": f"Bearer {bib_token}"}

    # Registrar socio
    client.post(
        "/api/v1/auth/registro",
        json={"nombre": "Socio Cob", "email": "socio_cob@example.com", "password": "Password1", "confirmar_password": "Password1"},
    )
    r_soc_log = client.post("/api/v1/auth/login", data={"username": "socio_cob@example.com", "password": "Password1"})
    soc_token = r_soc_log.json()["access_token"]
    soc_headers = {"Authorization": f"Bearer {soc_token}"}

    db.close()
    return {
        "admin_headers": adm_headers,
        "biblio_headers": bib_headers,
        "socio_headers": soc_headers,
    }


def test_cobertura_autores_y_categorias(client: TestClient, auth_tokens):
    bib_h = auth_tokens["biblio_headers"]
    adm_h = auth_tokens["admin_headers"]

    # Crear autor
    r = client.post("/api/v1/autores", json={"nombre": "Autor Test Cob", "nacionalidad": "Mexicana", "anio_nacimiento": 1950}, headers=bib_h)
    assert r.status_code == 201
    aid = r.json()["id"]

    # Conflicto nombre
    r_conf = client.post("/api/v1/autores", json={"nombre": "Autor Test Cob"}, headers=bib_h)
    assert r_conf.status_code == 409

    # Obtener por id
    r_get = client.get(f"/api/v1/autores/{aid}")
    assert r_get.status_code == 200
    assert r_get.json()["nombre"] == "Autor Test Cob"

    # Actualizar autor
    r_up = client.patch(f"/api/v1/autores/{aid}", json={"nacionalidad": "Argentina"}, headers=bib_h)
    assert r_up.status_code == 200
    assert r_up.json()["nacionalidad"] == "Argentina"

    # Eliminar autor
    r_del = client.delete(f"/api/v1/autores/{aid}", headers=adm_h)
    assert r_del.status_code == 204

    # No encontrado
    r_404 = client.get(f"/api/v1/autores/{aid}")
    assert r_404.status_code == 404

    # Categorías
    r_cat = client.post("/api/v1/categorias", json={"nombre": "Cat Cob", "descripcion": "Desc"}, headers=bib_h)
    assert r_cat.status_code == 201
    cid = r_cat.json()["id"]

    # Conflicto categoría
    r_cat_conf = client.post("/api/v1/categorias", json={"nombre": "Cat Cob"}, headers=bib_h)
    assert r_cat_conf.status_code == 409

    # Actualizar categoría
    r_cat_up = client.patch(f"/api/v1/categorias/{cid}", json={"descripcion": "Nueva Desc"}, headers=bib_h)
    assert r_cat_up.status_code == 200

    # Eliminar categoría
    r_cat_del = client.delete(f"/api/v1/categorias/{cid}", headers=adm_h)
    assert r_cat_del.status_code == 204


def test_cobertura_socios_me(client: TestClient, auth_tokens):
    soc_h = auth_tokens["socio_headers"]

    # GET /socios/me
    r_me = client.get("/api/v1/socios/me", headers=soc_h)
    assert r_me.status_code == 200
    assert r_me.json()["email"] == "socio_cob@example.com"

    # PATCH /socios/me válido
    r_patch = client.patch("/api/v1/socios/me", json={"nombre": "Socio Cob Actualizado", "telefono": "+573112223344"}, headers=soc_h)
    assert r_patch.status_code == 200
    assert r_patch.json()["nombre"] == "Socio Cob Actualizado"

    # GET /socios/me/prestamos
    r_p = client.get("/api/v1/socios/me/prestamos", headers=soc_h)
    assert r_p.status_code == 200

    # GET /socios/me/multas
    r_m = client.get("/api/v1/socios/me/multas", headers=soc_h)
    assert r_m.status_code == 200
    assert "total_adeudado" in r_m.json()


def test_cobertura_password_change(client: TestClient, auth_tokens):
    soc_h = auth_tokens["socio_headers"]

    # Cambiar password con contraseña actual incorrecta
    r_bad = client.patch("/api/v1/auth/me/password", json={"password_actual": "Wrong1234", "password_nueva": "NewPassword1"}, headers=soc_h)
    assert r_bad.status_code == 422

    # Cambiar password con éxito
    r_ok = client.patch("/api/v1/auth/me/password", json={"password_actual": "Password1", "password_nueva": "NewPassword1"}, headers=soc_h)
    assert r_ok.status_code == 200

    # Login con nueva contraseña
    r_new_log = client.post("/api/v1/auth/login", data={"username": "socio_cob@example.com", "password": "NewPassword1"})
    assert r_new_log.status_code == 200

    # Restaurar contraseña original
    new_h = {"Authorization": f"Bearer {r_new_log.json()['access_token']}"}
    client.patch("/api/v1/auth/me/password", json={"password_actual": "NewPassword1", "password_nueva": "Password1"}, headers=new_h)


def test_cobertura_reportes_detallados(client: TestClient, auth_tokens):
    bib_h = auth_tokens["biblio_headers"]

    assert client.get("/api/v1/reportes/libros-mas-prestados", headers=bib_h).status_code == 200
    assert client.get("/api/v1/reportes/categorias", headers=bib_h).status_code == 200
    assert client.get("/api/v1/reportes/prestamos-vencidos", headers=bib_h).status_code == 200
    assert client.get("/api/v1/reportes/socios-con-multas", headers=bib_h).status_code == 200
    assert client.get("/api/v1/reportes/autores", headers=bib_h).status_code == 200


def test_cobertura_usuarios_admin(client: TestClient, auth_tokens):
    adm_h = auth_tokens["admin_headers"]

    # Listar usuarios
    r_list = client.get("/api/v1/usuarios", headers=adm_h)
    assert r_list.status_code == 200
    assert "items" in r_list.json()

    # Filtro por rol
    r_rol = client.get("/api/v1/usuarios?rol=admin", headers=adm_h)
    assert r_rol.status_code == 200

    # Crear usuario con rol inválido (socio no permitido vía /usuarios)
    r_inv = client.post("/api/v1/usuarios", json={"nombre": "Invalido", "email": "inv@test.com", "password": "Password1", "rol": "socio"}, headers=adm_h)
    assert r_inv.status_code == 422
