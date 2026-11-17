import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.core.dependencies import get_db
from app.core.limiter import limiter
from app.main import app

settings = get_settings()
test_db_url = settings.test_database_url or settings.database_url
test_engine = create_engine(test_db_url)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def reset_rate_limiter():
    limiter.reset()
    yield


@pytest.fixture(scope="session")
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session", autouse=True)
def inicializar_bd_test():
    with test_engine.connect() as conn:
        conn.execute(
            text(
                "TRUNCATE refresh_tokens, usuarios, prestamos, libro_categoria, libros, categorias, socios, autores RESTART IDENTITY CASCADE;"
            )
        )
        conn.commit()
    yield
