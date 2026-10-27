from datetime import date, timedelta
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from app.core.database import Base, engine
from app.main import app


@pytest.fixture(scope="session", autouse=True)
def inicializar_bd():
    """Reinicia y crea las tablas limpias para la sesión de pruebas."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


def test_flujo_completo_24_casos(client: TestClient):
    # -------------------------------------------------------------
    # CARGA INICIAL DE DATOS
    # -------------------------------------------------------------
    # Autores:
    # 1. Gabriel García Márquez (Colombiana, 1927)
    # 2. Isabel Allende (Chilena, 1942)
    # 3. George Orwell (Británica, 1903)
    r_a1 = client.post("/autores", json={"nombre": "Gabriel García Márquez", "nacionalidad": "Colombiana", "anio_nacimiento": 1927})
    assert r_a1.status_code == 201
    a1_id = r_a1.json()["id"]

    r_a2 = client.post("/autores", json={"nombre": "Isabel Allende", "nacionalidad": "Chilena", "anio_nacimiento": 1942})
    assert r_a2.status_code == 201
    a2_id = r_a2.json()["id"]

    r_a3 = client.post("/autores", json={"nombre": "George Orwell", "nacionalidad": "Británica", "anio_nacimiento": 1903})
    assert r_a3.status_code == 201
    a3_id = r_a3.json()["id"]

    # Categorías:
    # 1. Novela
    # 2. Realismo Mágico
    # 3. Distopía
    # 4. Poesía
    r_c1 = client.post("/categorias", json={"nombre": "Novela"})
    assert r_c1.status_code == 201
    c1_id = r_c1.json()["id"]

    r_c2 = client.post("/categorias", json={"nombre": "Realismo Mágico"})
    assert r_c2.status_code == 201
    c2_id = r_c2.json()["id"]

    r_c3 = client.post("/categorias", json={"nombre": "Distopía"})
    assert r_c3.status_code == 201
    c3_id = r_c3.json()["id"]

    r_c4 = client.post("/categorias", json={"nombre": "Poesía"})
    assert r_c4.status_code == 201
    c4_id = r_c4.json()["id"]

    # Libros:
    # 1. Cien años de soledad (1967, 2 ejemplares, autor 1, categorías 1 y 2)
    r_l1 = client.post("/libros", json={
        "titulo": "Cien años de soledad",
        "isbn": "9780307474728",
        "anio_publicacion": 1967,
        "ejemplares": 2,
        "autor_id": a1_id,
        "categoria_ids": [c1_id, c2_id]
    })
    assert r_l1.status_code == 201
    l1_id = r_l1.json()["id"]

    # 2. El amor en los tiempos del cólera (1985, 1 ejemplar, autor 1, categoría 1)
    r_l2 = client.post("/libros", json={
        "titulo": "El amor en los tiempos del cólera",
        "isbn": "9780307389732",
        "anio_publicacion": 1985,
        "ejemplares": 1,
        "autor_id": a1_id,
        "categoria_ids": [c1_id]
    })
    assert r_l2.status_code == 201
    l2_id = r_l2.json()["id"]

    # 3. La casa de los espíritus (1982, 2 ejemplares, autor 2, categorías 1 y 2)
    r_l3 = client.post("/libros", json={
        "titulo": "La casa de los espíritus",
        "isbn": "9788401341991",
        "anio_publicacion": 1982,
        "ejemplares": 2,
        "autor_id": a2_id,
        "categoria_ids": [c1_id, c2_id]
    })
    assert r_l3.status_code == 201
    l3_id = r_l3.json()["id"]

    # 4. 1984 (1949, 3 ejemplares, autor 3, categorías 1 y 3)
    r_l4 = client.post("/libros", json={
        "titulo": "1984",
        "isbn": "9780451524935",
        "anio_publicacion": 1949,
        "ejemplares": 3,
        "autor_id": a3_id,
        "categoria_ids": [c1_id, c3_id]
    })
    assert r_l4.status_code == 201
    l4_id = r_l4.json()["id"]

    # Socios:
    # 1. Ana Torres (ANA@example.com)
    r_s1 = client.post("/socios", json={"nombre": "Ana Torres", "email": "ANA@example.com"})
    assert r_s1.status_code == 201
    s1_id = r_s1.json()["id"]

    # 2. Luis Pérez (luis@example.com)
    r_s2 = client.post("/socios", json={"nombre": "Luis Pérez", "email": "luis@example.com"})
    assert r_s2.status_code == 201
    s2_id = r_s2.json()["id"]

    # 3. Marta Ruiz (marta@example.com)
    r_s3 = client.post("/socios", json={"nombre": "Marta Ruiz", "email": "marta@example.com"})
    assert r_s3.status_code == 201
    s3_id = r_s3.json()["id"]

    # -------------------------------------------------------------
    # VERIFICACIÓN DE LOS 24 CASOS
    # -------------------------------------------------------------

    # Caso 1: POST /autores con "Gabriel García Márquez" otra vez -> 409
    res1 = client.post("/autores", json={"nombre": "Gabriel García Márquez"})
    assert res1.status_code == 409, f"Caso 1 falló: {res1.status_code} {res1.json()}"

    # Caso 2: POST /libros con "isbn": "123" -> 422
    res2 = client.post("/libros", json={
        "titulo": "Libro Erróneo",
        "isbn": "123",
        "anio_publicacion": 2000,
        "ejemplares": 1,
        "autor_id": a1_id,
        "categoria_ids": [c1_id]
    })
    assert res2.status_code == 422, f"Caso 2 falló: {res2.status_code}"

    # Caso 3: POST /libros con "categoria_ids": [1, 1] -> 422
    res3 = client.post("/libros", json={
        "titulo": "Libro Erróneo",
        "isbn": "1111111111111",
        "anio_publicacion": 2000,
        "ejemplares": 1,
        "autor_id": a1_id,
        "categoria_ids": [c1_id, c1_id]
    })
    assert res3.status_code == 422, f"Caso 3 falló: {res3.status_code}"

    # Caso 4: POST /libros con "autor_id": 99 -> 404
    res4 = client.post("/libros", json={
        "titulo": "Libro Sin Autor",
        "isbn": "2222222222222",
        "anio_publicacion": 2000,
        "ejemplares": 1,
        "autor_id": 99,
        "categoria_ids": [c1_id]
    })
    assert res4.status_code == 404, f"Caso 4 falló: {res4.status_code}"

    # Caso 5: GET /libros?categoria_id=2&orden=-anio -> Los 2 libros de realismo mágico, el más nuevo primero
    res5 = client.get(f"/libros?categoria_id={c2_id}&orden=-anio")
    assert res5.status_code == 200
    libros_rm = res5.json()
    assert len(libros_rm) == 2, f"Esperados 2 libros, obtenidos: {len(libros_rm)}"
    assert libros_rm[0]["titulo"] == "La Casa De Los Espíritus"
    assert libros_rm[0]["anio_publicacion"] == 1982
    assert libros_rm[1]["titulo"] == "Cien Años De Soledad"
    assert libros_rm[1]["anio_publicacion"] == 1967

    # Caso 6: GET /libros?autor=gabriel -> Los 2 libros de García Márquez
    res6 = client.get("/libros?autor=gabriel")
    assert res6.status_code == 200
    libros_gabriel = res6.json()
    assert len(libros_gabriel) == 2, f"Esperados 2 libros de García Márquez, obtenidos: {len(libros_gabriel)}"
    titulos_gabriel = {l["titulo"] for l in libros_gabriel}
    assert "Cien Años De Soledad" in titulos_gabriel
    assert "El Amor En Los Tiempos Del Cólera" in titulos_gabriel

    # Caso 7: Préstamo del libro 2 al socio 1 -> 201, estado activo
    res7 = client.post("/prestamos", json={
        "libro_id": l2_id,
        "socio_id": s1_id,
        "dias": 14
    })
    assert res7.status_code == 201, f"Caso 7 falló: {res7.status_code} {res7.json()}"
    assert res7.json()["estado"] == "activo"

    # Caso 8: Préstamo del libro 2 al socio 2 -> 422, no hay ejemplares
    res8 = client.post("/prestamos", json={
        "libro_id": l2_id,
        "socio_id": s2_id,
        "dias": 14
    })
    assert res8.status_code == 422, f"Caso 8 falló: {res8.status_code} {res8.json()}"
    assert "no hay ejemplares disponibles" in res8.json()["detail"].lower()

    # Caso 9: GET /libros/2 -> disponibles: 0
    res9 = client.get(f"/libros/{l2_id}")
    assert res9.status_code == 200
    assert res9.json()["disponibles"] == 0, f"Caso 9 falló: disponibles={res9.json()['disponibles']}"

    # Caso 10: Préstamo del libro 1 al socio 2 con fecha_prestamo de hace 20 días y dias: 7 -> 201, estado vencido
    hace_20_dias = date.today() - timedelta(days=20)
    res10 = client.post("/prestamos", json={
        "libro_id": l1_id,
        "socio_id": s2_id,
        "fecha_prestamo": hace_20_dias.isoformat(),
        "dias": 7
    })
    assert res10.status_code == 201, f"Caso 10 falló: {res10.status_code} {res10.json()}"
    p_caso10 = res10.json()
    assert p_caso10["estado"] == "vencido"
    p10_id = p_caso10["id"]

    # Caso 11: Préstamo del libro 4 al socio 2 -> 422, tiene préstamos vencidos
    res11 = client.post("/prestamos", json={
        "libro_id": l4_id,
        "socio_id": s2_id,
        "dias": 14
    })
    assert res11.status_code == 422, f"Caso 11 falló: {res11.status_code} {res11.json()}"
    assert "tiene préstamos vencidos" in res11.json()["detail"].lower()

    # Caso 12: GET /reportes/prestamos-vencidos -> Aparece el préstamo del caso 10 con dias_retraso: 13
    res12 = client.get("/reportes/prestamos-vencidos")
    assert res12.status_code == 200
    vencidos = res12.json()
    prestamo_vencido = next((p for p in vencidos if p["prestamo_id"] == p10_id), None)
    assert prestamo_vencido is not None, f"Caso 12 falló: préstamo {p10_id} no está en vencidos"
    assert prestamo_vencido["dias_retraso"] == 13, f"Esperados 13 días de retraso, obtenidos: {prestamo_vencido['dias_retraso']}"

    # Caso 13: Devolver hoy el préstamo del caso 10 -> 200, multa: 6.5
    res13 = client.post(f"/prestamos/{p10_id}/devolucion", json={
        "fecha_devolucion": date.today().isoformat()
    })
    assert res13.status_code == 200, f"Caso 13 falló: {res13.status_code} {res13.json()}"
    multa_dev = float(res13.json()["multa"])
    assert multa_dev == 6.5, f"Esperada multa 6.5, obtenida: {multa_dev}"

    # Caso 14: Devolverlo otra vez -> 409
    res14 = client.post(f"/prestamos/{p10_id}/devolucion", json={})
    assert res14.status_code == 409, f"Caso 14 falló: {res14.status_code} {res14.json()}"

    # Caso 15: Socio 3: préstamos de los libros 1, 3 y 4, y luego un cuarto -> El cuarto responde 422 (máximo 3)
    p_s3_1 = client.post("/prestamos", json={"libro_id": l1_id, "socio_id": s3_id, "dias": 14})
    assert p_s3_1.status_code == 201
    p_s3_2 = client.post("/prestamos", json={"libro_id": l3_id, "socio_id": s3_id, "dias": 14})
    assert p_s3_2.status_code == 201
    p_s3_3 = client.post("/prestamos", json={"libro_id": l4_id, "socio_id": s3_id, "dias": 14})
    assert p_s3_3.status_code == 201

    # Intentar un 4to préstamo al socio 3 (ej. libro 3 disponible aún o libro 4)
    res15 = client.post("/prestamos", json={"libro_id": l3_id, "socio_id": s3_id, "dias": 14})
    assert res15.status_code == 422, f"Caso 15 falló: {res15.status_code} {res15.json()}"
    assert "máximo de 3 préstamos" in res15.json()["detail"].lower()

    # Caso 16: PATCH /libros/4 con "ejemplares": 0 -> 422
    res16 = client.patch(f"/libros/{l4_id}", json={"ejemplares": 0})
    assert res16.status_code == 422, f"Caso 16 falló: {res16.status_code} {res16.json()}"

    # Caso 17: DELETE /autores/1 -> 409, tiene libros
    res17 = client.delete(f"/autores/{a1_id}")
    assert res17.status_code == 409, f"Caso 17 falló: {res17.status_code} {res17.json()}"

    # Caso 18: DELETE /libros/2 -> 409, préstamo sin devolver
    res18 = client.delete(f"/libros/{l2_id}")
    assert res18.status_code == 409, f"Caso 18 falló: {res18.status_code} {res18.json()}"

    # Caso 19: DELETE /socios/2 -> 204 y queda activo: false
    res19 = client.delete(f"/socios/{s2_id}")
    assert res19.status_code == 204, f"Caso 19 falló: {res19.status_code}"
    # Verificar que el socio 2 sigue existiendo pero con activo=False
    socio2_get = client.get(f"/socios/{s2_id}")
    assert socio2_get.status_code == 200
    assert socio2_get.json()["activo"] is False, f"Caso 19 falló: activo={socio2_get.json()['activo']}"

    # Caso 20: Cualquier préstamo al socio 2 -> 422, el socio no está activo
    res20 = client.post("/prestamos", json={"libro_id": l1_id, "socio_id": s2_id, "dias": 14})
    assert res20.status_code == 422, f"Caso 20 falló: {res20.status_code} {res20.json()}"
    assert "el socio no está activo" in res20.json()["detail"].lower()

    # Caso 21: GET /reportes/categorias -> poesía aparece con total_libros: 0
    res21 = client.get("/reportes/categorias")
    assert res21.status_code == 200
    categorias_rep = res21.json()
    poesia = next((c for c in categorias_rep if c["nombre"] == "poesía"), None)
    assert poesia is not None, "Categoría poesía no encontrada en reporte"
    assert poesia["total_libros"] == 0, f"Esperado 0 libros en poesía, obtenido: {poesia['total_libros']}"

    # Caso 22: GET /reportes/socios-con-multas -> Solo Luis Pérez, total_multas: 6.5
    res22 = client.get("/reportes/socios-con-multas")
    assert res22.status_code == 200
    multados = res22.json()
    assert len(multados) == 1, f"Esperado 1 socio con multas, obtenidos: {len(multados)}"
    assert multados[0]["nombre"] == "Luis Pérez"
    assert float(multados[0]["total_multas"]) == 6.5

    # Caso 23: GET /reportes/libros-mas-prestados?limite=3 -> 3 libros ordenados de mayor a menor
    res23 = client.get("/reportes/libros-mas-prestados?limite=3")
    assert res23.status_code == 200
    mas_prestados = res23.json()
    assert len(mas_prestados) == 3, f"Esperados 3 libros más prestados, obtenidos: {len(mas_prestados)}"
    # Verificar orden descendente por total_prestamos
    assert mas_prestados[0]["total_prestamos"] >= mas_prestados[1]["total_prestamos"]
    assert mas_prestados[1]["total_prestamos"] >= mas_prestados[2]["total_prestamos"]

    # Caso 24: GET /libros?skip=0&limit=2 y luego ?skip=2&limit=2 -> 2 libros en cada página, sin repetir
    res24_p1 = client.get("/libros?skip=0&limit=2")
    assert res24_p1.status_code == 200
    pag1 = res24_p1.json()
    assert len(pag1) == 2, f"Esperados 2 libros en página 1, obtenidos: {len(pag1)}"

    res24_p2 = client.get("/libros?skip=2&limit=2")
    assert res24_p2.status_code == 200
    pag2 = res24_p2.json()
    assert len(pag2) == 2, f"Esperados 2 libros en página 2, obtenidos: {len(pag2)}"

    ids_p1 = {l["id"] for l in pag1}
    ids_p2 = {l["id"] for l in pag2}
    assert ids_p1.isdisjoint(ids_p2), f"Los libros no deben repetirse entre páginas: {ids_p1} y {ids_p2}"

    # Verificación adicional de reportes de autores y resumen
    res_autores = client.get("/reportes/autores")
    assert res_autores.status_code == 200
    assert len(res_autores.json()) == 3

    res_resumen = client.get("/reportes/resumen")
    assert res_resumen.status_code == 200
    resumen = res_resumen.json()
    assert resumen["total_libros"] == 4
    assert resumen["total_ejemplares"] == 8
    assert resumen["socios_activos"] == 2
    assert float(resumen["total_multas"]) == 6.5

    print("\n¡LOS 24 CASOS DE PRUEBA Y TODOS LOS REPORTES PASARON EXITOSAMENTE!")
