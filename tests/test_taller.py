from datetime import date, timedelta
from decimal import Decimal
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import SessionLocal
from app.core.limiter import limiter
from app.core.security import hashear_password
from app.models.usuario import RolUsuario, Usuario
from tests.conftest import TestingSessionLocal


def test_flujo_completo_33_casos(client: TestClient):
    settings = get_settings()
    limiter.reset()

    # -------------------------------------------------------------
    # PASO PREVIO 1: Crear el Administrador
    # -------------------------------------------------------------
    db = TestingSessionLocal()
    admin_usuario = Usuario(
        email="admin@biblioteca.com",
        nombre="Admin Principal",
        password_hash=hashear_password("Admin1234"),
        rol=RolUsuario.admin,
        activo=True,
    )
    db.add(admin_usuario)
    db.commit()
    db.refresh(admin_usuario)
    admin_id = admin_usuario.id
    db.close()

    # Login como Admin para obtener token
    r_admin_login = client.post("/api/v1/auth/login", data={"username": "admin@biblioteca.com", "password": "Admin1234"})
    assert r_admin_login.status_code == 200
    admin_token = r_admin_login.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # -------------------------------------------------------------
    # PASO PREVIO 2: Crear el Bibliotecario con el token del Admin
    # -------------------------------------------------------------
    r_biblio = client.post(
        "/api/v1/usuarios",
        json={
            "email": "biblio@biblioteca.com",
            "nombre": "Bibliotecario Uno",
            "password": "Biblio1234",
            "rol": "bibliotecario",
        },
        headers=admin_headers,
    )
    assert r_biblio.status_code == 201
    biblio_id = r_biblio.json()["id"]

    # Login como Bibliotecario
    r_biblio_login = client.post("/api/v1/auth/login", data={"username": "biblio@biblioteca.com", "password": "Biblio1234"})
    assert r_biblio_login.status_code == 200
    biblio_token = r_biblio_login.json()["access_token"]
    biblio_headers = {"Authorization": f"Bearer {biblio_token}"}

    # -------------------------------------------------------------
    # CASO 1: Registro con password "abcdefgh" -> 422
    # -------------------------------------------------------------
    r1 = client.post(
        "/api/v1/auth/registro",
        json={
            "nombre": "Prueba",
            "email": "prueba1@example.com",
            "password": "abcdefgh",
            "confirmar_password": "abcdefgh",
        },
    )
    assert r1.status_code == 422

    # -------------------------------------------------------------
    # CASO 2: Registro con password y confirmar_password distintos -> 422
    # -------------------------------------------------------------
    r2 = client.post(
        "/api/v1/auth/registro",
        json={
            "nombre": "Prueba",
            "email": "prueba2@example.com",
            "password": "Password1",
            "confirmar_password": "Password2",
        },
    )
    assert r2.status_code == 422

    # -------------------------------------------------------------
    # CASO 3: Registro válido de Ana -> 201, rol socio, socio_id con valor
    # -------------------------------------------------------------
    r3 = client.post(
        "/api/v1/auth/registro",
        json={
            "nombre": "Ana Torres",
            "email": "ana@example.com",
            "telefono": "+573001112233",
            "password": "Password1",
            "confirmar_password": "Password1",
        },
    )
    assert r3.status_code == 201
    ana_data = r3.json()
    assert ana_data["rol"] == "socio"
    assert ana_data["socio_id"] is not None
    assert "password_hash" not in ana_data
    assert "password" not in ana_data
    ana_socio_id = ana_data["socio_id"]
    ana_user_id = ana_data["id"]

    # Registrar a Luis Pérez
    r_luis_reg = client.post(
        "/api/v1/auth/registro",
        json={
            "nombre": "Luis Pérez",
            "email": "luis@example.com",
            "password": "Password1",
            "confirmar_password": "Password1",
        },
    )
    assert r_luis_reg.status_code == 201
    luis_data = r_luis_reg.json()
    luis_socio_id = luis_data["socio_id"]
    luis_user_id = luis_data["id"]

    # -------------------------------------------------------------
    # CASO 4: Registro de Ana otra vez con "ANA@EXAMPLE.COM" -> 409
    # -------------------------------------------------------------
    r4 = client.post(
        "/api/v1/auth/registro",
        json={
            "nombre": "Ana Torres",
            "email": "ANA@EXAMPLE.COM",
            "password": "Password1",
            "confirmar_password": "Password1",
        },
    )
    assert r4.status_code == 409

    # -------------------------------------------------------------
    # CASO 5: Login de Ana con contraseña incorrecta -> 401 "Credenciales inválidas"
    # -------------------------------------------------------------
    r5 = client.post("/api/v1/auth/login", data={"username": "ana@example.com", "password": "WrongPassword1"})
    assert r5.status_code == 401
    assert r5.json()["detail"] == "Credenciales inválidas"

    # -------------------------------------------------------------
    # CASO 6: Login con un email que no existe -> 401 mismo mensaje
    # -------------------------------------------------------------
    r6 = client.post("/api/v1/auth/login", data={"username": "inexistente@example.com", "password": "Password1"})
    assert r6.status_code == 401
    assert r6.json()["detail"] == "Credenciales inválidas"

    # -------------------------------------------------------------
    # CASO 7: Login correcto de Ana -> 200 con tokens
    # -------------------------------------------------------------
    r7 = client.post("/api/v1/auth/login", data={"username": "ana@example.com", "password": "Password1"})
    assert r7.status_code == 200
    toks_ana = r7.json()
    assert "access_token" in toks_ana
    assert "refresh_token" in toks_ana
    assert toks_ana["token_type"].lower() == "bearer"
    ana_token = toks_ana["access_token"]
    ana_refresh = toks_ana["refresh_token"]
    ana_headers = {"Authorization": f"Bearer {ana_token}"}

    # -------------------------------------------------------------
    # CASO 8: GET /auth/me sin token -> 401 y cabecera WWW-Authenticate: Bearer
    # -------------------------------------------------------------
    r8 = client.get("/api/v1/auth/me")
    assert r8.status_code == 401
    assert "bearer" in r8.headers.get("www-authenticate", "").lower()

    # -------------------------------------------------------------
    # CASO 9: GET /auth/me con el token alterado en un carácter -> 401
    # -------------------------------------------------------------
    r9 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {ana_token}a"})
    assert r9.status_code == 401

    # -------------------------------------------------------------
    # CASO 10: GET /auth/me usando el refresh_token como Bearer -> 401
    # -------------------------------------------------------------
    r10 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {ana_refresh}"})
    assert r10.status_code == 401

    # -------------------------------------------------------------
    # CARGA INICIAL DE CATÁLOGO con token de Bibliotecario
    # -------------------------------------------------------------
    r_aut1 = client.post("/api/v1/autores", json={"nombre": "Gabriel García Márquez", "nacionalidad": "Colombiana", "anio_nacimiento": 1927}, headers=biblio_headers)
    assert r_aut1.status_code == 201
    aut1_id = r_aut1.json()["id"]

    r_aut2 = client.post("/api/v1/autores", json={"nombre": "George Orwell", "nacionalidad": "Británica", "anio_nacimiento": 1903}, headers=biblio_headers)
    assert r_aut2.status_code == 201
    aut2_id = r_aut2.json()["id"]

    r_cat1 = client.post("/api/v1/categorias", json={"nombre": "Novela", "descripcion": "Narrativa"}, headers=biblio_headers)
    assert r_cat1.status_code == 201
    cat1_id = r_cat1.json()["id"]

    r_cat2 = client.post("/api/v1/categorias", json={"nombre": "Distopía", "descripcion": "Ficción"}, headers=biblio_headers)
    assert r_cat2.status_code == 201
    cat2_id = r_cat2.json()["id"]

    # -------------------------------------------------------------
    # CASO 11: GET /libros sin token -> 200 con items, total, skip y limit
    # -------------------------------------------------------------
    r11 = client.get("/api/v1/libros")
    assert r11.status_code == 200
    libros_data = r11.json()
    assert "items" in libros_data
    assert "total" in libros_data
    assert "skip" in libros_data
    assert "limit" in libros_data

    # -------------------------------------------------------------
    # CASO 12: POST /libros con token de Ana -> 403
    # -------------------------------------------------------------
    r12 = client.post(
        "/api/v1/libros",
        json={
            "titulo": "Cien Años De Soledad",
            "isbn": "9780307474728",
            "anio_publicacion": 1967,
            "ejemplares": 2,
            "autor_id": aut1_id,
            "categoria_ids": [cat1_id],
        },
        headers=ana_headers,
    )
    assert r12.status_code == 403

    # -------------------------------------------------------------
    # CASO 13: POST /libros con token del bibliotecario -> 201
    # -------------------------------------------------------------
    r13 = client.post(
        "/api/v1/libros",
        json={
            "titulo": "Cien Años De Soledad",
            "isbn": "9780307474728",
            "anio_publicacion": 1967,
            "ejemplares": 2,
            "autor_id": aut1_id,
            "categoria_ids": [cat1_id],
        },
        headers=biblio_headers,
    )
    assert r13.status_code == 201
    libro1_id = r13.json()["id"]

    # Crear segundo libro para Luis
    r_l2 = client.post(
        "/api/v1/libros",
        json={
            "titulo": "1984",
            "isbn": "9780451524935",
            "anio_publicacion": 1949,
            "ejemplares": 3,
            "autor_id": aut2_id,
            "categoria_ids": [cat2_id],
        },
        headers=biblio_headers,
    )
    assert r_l2.status_code == 201
    libro2_id = r_l2.json()["id"]

    # -------------------------------------------------------------
    # CASO 14: DELETE /libros/{id} con token del bibliotecario -> 403
    # -------------------------------------------------------------
    r14 = client.delete(f"/api/v1/libros/{libro1_id}", headers=biblio_headers)
    assert r14.status_code == 403

    # -------------------------------------------------------------
    # CASO 15: El bibliotecario registra un préstamo a Ana -> 201 y registrado_por_id
    # -------------------------------------------------------------
    r15 = client.post(
        "/api/v1/prestamos",
        json={
            "libro_id": libro1_id,
            "socio_id": ana_socio_id,
            "dias": 14,
        },
        headers=biblio_headers,
    )
    assert r15.status_code == 201
    prestamo_ana = r15.json()
    assert prestamo_ana["registrado_por_id"] == biblio_id
    prestamo_ana_id = prestamo_ana["id"]

    # -------------------------------------------------------------
    # CASO 16: El bibliotecario registra un préstamo a Luis -> 201
    # -------------------------------------------------------------
    r16 = client.post(
        "/api/v1/prestamos",
        json={
            "libro_id": libro2_id,
            "socio_id": luis_socio_id,
            "dias": 14,
        },
        headers=biblio_headers,
    )
    assert r16.status_code == 201
    prestamo_luis_id = r16.json()["id"]

    # -------------------------------------------------------------
    # CASO 17: GET /prestamos con token de Ana -> Solo el préstamo de Ana (total: 1)
    # -------------------------------------------------------------
    r17 = client.get("/api/v1/prestamos", headers=ana_headers)
    assert r17.status_code == 200
    res17 = r17.json()
    assert res17["total"] == 1
    assert len(res17["items"]) == 1
    assert res17["items"][0]["id"] == prestamo_ana_id

    # -------------------------------------------------------------
    # CASO 18: GET /prestamos?socio_id={Luis} con token de Ana -> Solo los préstamos de Ana
    # -------------------------------------------------------------
    r18 = client.get(f"/api/v1/prestamos?socio_id={luis_socio_id}", headers=ana_headers)
    assert r18.status_code == 200
    res18 = r18.json()
    assert res18["total"] == 1
    assert res18["items"][0]["socio_id"] == ana_socio_id

    # -------------------------------------------------------------
    # CASO 19: GET /prestamos/{id del préstamo de Luis} con token de Ana -> 404
    # -------------------------------------------------------------
    r19 = client.get(f"/api/v1/prestamos/{prestamo_luis_id}", headers=ana_headers)
    assert r19.status_code == 404

    # -------------------------------------------------------------
    # CASO 20: PATCH /socios/me con { "activo": false } con token de Ana -> 422
    # -------------------------------------------------------------
    r20 = client.patch("/api/v1/socios/me", json={"activo": False}, headers=ana_headers)
    assert r20.status_code == 422

    # -------------------------------------------------------------
    # CASO 21: POST /auth/refresh con el refresh de Ana -> 200 con un par nuevo
    # -------------------------------------------------------------
    r21 = client.post("/api/v1/auth/refresh", json={"refresh_token": ana_refresh})
    assert r21.status_code == 200
    toks_nuevos_ana = r21.json()
    nuevo_ana_at = toks_nuevos_ana["access_token"]
    nuevo_ana_rt = toks_nuevos_ana["refresh_token"]
    assert nuevo_ana_at != ana_token
    assert nuevo_ana_rt != ana_refresh

    # -------------------------------------------------------------
    # CASO 22: POST /auth/refresh otra vez con el refresh anterior -> 401 y todos revocados
    # -------------------------------------------------------------
    r22_reuso = client.post("/api/v1/auth/refresh", json={"refresh_token": ana_refresh})
    assert r22_reuso.status_code == 401

    # Verificar que el nuevo refresh también quedó revocado por detección de robo
    r22_nuevo_revocado = client.post("/api/v1/auth/refresh", json={"refresh_token": nuevo_ana_rt})
    assert r22_nuevo_revocado.status_code == 401

    # -------------------------------------------------------------
    # CASO 23: Login de Ana, logout y luego refresh con ese token -> 401
    # -------------------------------------------------------------
    r23_login = client.post("/api/v1/auth/login", data={"username": "ana@example.com", "password": "Password1"})
    assert r23_login.status_code == 200
    rt_logout_test = r23_login.json()["refresh_token"]

    r23_logout = client.post("/api/v1/auth/logout", json={"refresh_token": rt_logout_test})
    assert r23_logout.status_code == 204

    r23_refresh_revocado = client.post("/api/v1/auth/refresh", json={"refresh_token": rt_logout_test})
    assert r23_refresh_revocado.status_code == 401

    # -------------------------------------------------------------
    # CASO 24: Luis falla el login 5 veces y luego usa la contraseña correcta -> 423
    # -------------------------------------------------------------
    limiter.reset()
    for _ in range(5):
        client.post("/api/v1/auth/login", data={"username": "luis@example.com", "password": "PasswordInvalida"})

    r24 = client.post("/api/v1/auth/login", data={"username": "luis@example.com", "password": "Password1"})
    assert r24.status_code == 423
    assert "bloqueada" in r24.json()["detail"].lower()

    # -------------------------------------------------------------
    # CASO 25: 11 peticiones de login en menos de un minuto -> La 11.ª responde 429
    # -------------------------------------------------------------
    limiter.reset()
    for i in range(10):
        client.post("/api/v1/auth/login", data={"username": f"rate_limit_{i}@example.com", "password": "BadPassword"})
    r25 = client.post("/api/v1/auth/login", data={"username": "rate_limit_11@example.com", "password": "BadPassword"})
    assert r25.status_code == 429
    limiter.reset()

    # -------------------------------------------------------------
    # CASO 26: El admin desactiva a Luis; Luis usa su access token en /auth/me -> 403
    # -------------------------------------------------------------
    # Desbloquear y obtener token de Luis
    db = TestingSessionLocal()
    u_luis = db.get(Usuario, luis_user_id)
    u_luis.bloqueado_hasta = None
    u_luis.intentos_fallidos = 0
    u_luis.activo = True
    db.commit()
    db.close()

    r_luis_log = client.post("/api/v1/auth/login", data={"username": "luis@example.com", "password": "Password1"})
    assert r_luis_log.status_code == 200
    luis_token = r_luis_log.json()["access_token"]
    luis_headers = {"Authorization": f"Bearer {luis_token}"}

    # Admin desactiva a Luis
    r_desactivar = client.patch(f"/api/v1/usuarios/{luis_user_id}/activo", json={"activo": False}, headers=admin_headers)
    assert r_desactivar.status_code == 200

    # Luis intenta usar su access token vigente
    r26 = client.get("/api/v1/auth/me", headers=luis_headers)
    assert r26.status_code == 403
    assert r26.json()["detail"] == "Usuario inactivo"

    # Reactivar a Luis para pruebas posteriores
    client.patch(f"/api/v1/usuarios/{luis_user_id}/activo", json={"activo": True}, headers=admin_headers)

    # -------------------------------------------------------------
    # CASO 27: El admin se cambia a sí mismo el rol a socio -> 422
    # -------------------------------------------------------------
    r27 = client.patch(f"/api/v1/usuarios/{admin_id}/rol", json={"rol": "socio"}, headers=admin_headers)
    assert r27.status_code == 422

    # -------------------------------------------------------------
    # CASO 28: GET /reportes/resumen con token de Ana / del bibliotecario -> 403 / 200
    # -------------------------------------------------------------
    # Obtener token fresco de Ana
    r_ana_login2 = client.post("/api/v1/auth/login", data={"username": "ana@example.com", "password": "Password1"})
    ana_headers = {"Authorization": f"Bearer {r_ana_login2.json()['access_token']}"}

    r28_ana = client.get("/api/v1/reportes/resumen", headers=ana_headers)
    assert r28_ana.status_code == 403

    r28_biblio = client.get("/api/v1/reportes/resumen", headers=biblio_headers)
    assert r28_biblio.status_code == 200
    assert "total_libros" in r28_biblio.json()

    # -------------------------------------------------------------
    # CASO 29: Préstamo con fecha de hace 20 días y dias: 7; devolverlo hoy (multa 6.5) y pedir otro -> 422
    # -------------------------------------------------------------
    # Devolver el primer préstamo de Ana para no chocar con límite de ejemplares o préstamos
    client.post(f"/api/v1/prestamos/{prestamo_ana_id}/devolucion", json={"fecha_devolucion": str(date.today())}, headers=biblio_headers)

    fecha_hace_20 = date.today() - timedelta(days=20)
    r29_crear = client.post(
        "/api/v1/prestamos",
        json={
            "libro_id": libro1_id,
            "socio_id": ana_socio_id,
            "fecha_prestamo": str(fecha_hace_20),
            "dias": 7,
        },
        headers=biblio_headers,
    )
    assert r29_crear.status_code == 201
    p29_id = r29_crear.json()["id"]

    # Devolverlo hoy
    r29_dev = client.post(f"/api/v1/prestamos/{p29_id}/devolucion", json={"fecha_devolucion": str(date.today())}, headers=biblio_headers)
    assert r29_dev.status_code == 200
    assert Decimal(str(r29_dev.json()["multa"])) == Decimal("6.50")
    assert r29_dev.json()["multa_pagada"] is False

    # Ana intenta pedir otro libro teniendo multas pendientes -> 422
    r29_bloqueo = client.post(
        "/api/v1/prestamos",
        json={
            "libro_id": libro2_id,
            "socio_id": ana_socio_id,
            "dias": 14,
        },
        headers=biblio_headers,
    )
    assert r29_bloqueo.status_code == 422
    assert "multas pendientes" in r29_bloqueo.json()["detail"].lower()

    # -------------------------------------------------------------
    # CASO 30: POST /prestamos/{id}/pago-multa y repetir préstamo del caso 29 -> 200 y luego 201
    # -------------------------------------------------------------
    r30_pago = client.post(f"/api/v1/prestamos/{p29_id}/pago-multa", headers=biblio_headers)
    assert r30_pago.status_code == 200
    assert r30_pago.json()["multa_pagada"] is True

    r30_repetir = client.post(
        "/api/v1/prestamos",
        json={
            "libro_id": libro2_id,
            "socio_id": ana_socio_id,
            "dias": 14,
        },
        headers=biblio_headers,
    )
    assert r30_repetir.status_code == 201

    # -------------------------------------------------------------
    # CASO 31: GET /api/v1/health -> 200 { "status": "ok", "database": "ok" }
    # -------------------------------------------------------------
    r31 = client.get("/api/v1/health")
    assert r31.status_code == 200
    assert r31.json() == {"status": "ok", "database": "ok"}

    # -------------------------------------------------------------
    # CASO 32: alembic downgrade base y alembic upgrade head -> Ambos sin errores
    # -------------------------------------------------------------
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", settings.test_database_url or settings.database_url)
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
