# Tests de la API de gestión de tareas con pytest y FastAPI TestClient
#
# COBERTURA ACTUAL: solo happy path básico
#   - POST /tasks  → crear tarea correctamente
#   - GET  /tasks  → listar tareas
#
# PENDIENTE DE CUBRIR:
#   - POST /tasks con título vacío o menor de 3 caracteres (error 422)
#   - GET  /tasks/{id} con id inexistente (error 404)
#   - PATCH /tasks/{id} sobre una tarea con estado "done" (error 400)
#   - PATCH /tasks/{id} con id inexistente (error 404)
#   - DELETE /tasks/{id} con id inexistente (error 404)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from aplicacion.base_de_datos import Base, get_db
from aplicacion.principal import app

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test_tareas.db"

engine_test = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Happy path: crear tarea
# ---------------------------------------------------------------------------

def test_crear_tarea_correctamente(client):
    payload = {"title": "Tarea de prueba", "description": "Descripción de ejemplo"}
    response = client.post("/tasks/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Tarea de prueba"
    assert data["description"] == "Descripción de ejemplo"
    assert data["status"] == "pending"
    assert "id" in data
    assert "created_at" in data


# ---------------------------------------------------------------------------
# Happy path: listar tareas
# ---------------------------------------------------------------------------

def test_listar_tareas_con_datos(client):
    client.post("/tasks/", json={"title": "Tarea uno"})
    client.post("/tasks/", json={"title": "Tarea dos"})

    response = client.get("/tasks/")
    assert response.status_code == 200
    assert len(response.json()) == 2


# ---------------------------------------------------------------------------
# TODO: implementar los siguientes tests de casos de error
# ---------------------------------------------------------------------------

def test_crear_tarea_titulo_vacio(client):
    # TODO: verificar que POST /tasks con título "" devuelve 422
    pass


def test_crear_tarea_titulo_corto(client):
    # TODO: verificar que POST /tasks con título < 3 caracteres devuelve 422
    pass


def test_obtener_tarea_no_encontrada(client):
    # TODO: verificar que GET /tasks/9999 devuelve 404
    pass


def test_actualizar_tarea_completada(client):
    # TODO: verificar que PATCH sobre tarea con estado done devuelve 409
    pass


def test_actualizar_tarea_no_encontrada(client):
    # TODO: verificar que PATCH /tasks/9999 devuelve 404
    pass


def test_eliminar_tarea_no_encontrada(client):
    # TODO: verificar que DELETE /tasks/9999 devuelve 404
    pass
