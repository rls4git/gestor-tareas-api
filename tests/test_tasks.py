# Tests de la API de gestión de tareas con pytest y FastAPI TestClient
#
# COBERTURA:
#   Happy path
#   - POST   /tasks       → crear tarea correctamente (201)
#   - POST   /tasks       → crear con solo título, description=None (201)
#   - POST   /tasks       → crear con estado explícito in_progress (201)
#   - GET    /tasks/{id}  → obtener tarea existente (200)
#   - PATCH  /tasks/{id}  → actualizar campos parciales (200)
#   - PATCH  /tasks/{id}  → body vacío, sin cambios (200)
#   - PATCH  /tasks/{id}  → cambiar estado a in_progress (200)
#   - DELETE /tasks/{id}  → eliminar tarea existente (204)
#
#   Errores y casos límite
#   - POST   /tasks       → sin campo título (422)
#   - POST   /tasks       → título vacío (422, validación min 3 chars)
#   - POST   /tasks       → título menor a 3 caracteres (422)
#   - POST   /tasks       → estado inválido (422)
#   - GET    /tasks       → bug: siempre devuelve lista vacía
#   - GET    /tasks/{id}  → id inexistente (404)
#   - PATCH  /tasks/{id}  → intentar establecer status a "done" (400)
#   - PATCH  /tasks/{id}  → estado inválido (422)
#   - PATCH  /tasks/{id}  → id inexistente (404)
#   - DELETE /tasks/{id}  → id inexistente (404)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from aplicacion.base_de_datos import Base, get_db
from aplicacion.principal import app

# StaticPool garantiza que todas las sesiones comparten la misma conexión en memoria
engine_test = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine_test)
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine_test)


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


def test_crear_tarea_solo_titulo(client):
    response = client.post("/tasks/", json={"title": "Solo título"})

    assert response.status_code == 201
    assert response.json()["description"] is None
    assert response.json()["status"] == "pending"


def test_crear_tarea_estado_explicito(client):
    response = client.post(
        "/tasks/", json={"title": "En progreso", "status": "in_progress"}
    )

    assert response.status_code == 201
    assert response.json()["status"] == "in_progress"


# ---------------------------------------------------------------------------
# Happy path: obtener, actualizar y eliminar tarea
# ---------------------------------------------------------------------------

def test_obtener_tarea_existente(client):
    created = client.post(
        "/tasks/", json={"title": "Tarea detalle", "description": "Desc"}
    ).json()

    response = client.get(f"/tasks/{created['id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == created["id"]
    assert data["title"] == "Tarea detalle"
    assert data["description"] == "Desc"
    assert data["status"] == "pending"
    assert "created_at" in data


def test_actualizar_tarea_campos_parciales(client):
    created = client.post(
        "/tasks/", json={"title": "Original", "description": "Desc original"}
    ).json()

    response = client.patch(
        f"/tasks/{created['id']}", json={"description": "Desc nueva"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Original"
    assert data["description"] == "Desc nueva"


def test_actualizar_tarea_body_vacio(client):
    created = client.post("/tasks/", json={"title": "Intacta"}).json()

    response = client.patch(f"/tasks/{created['id']}", json={})

    assert response.status_code == 200
    assert response.json()["title"] == "Intacta"


def test_actualizar_tarea_estado_in_progress(client):
    created = client.post("/tasks/", json={"title": "Cambiar estado"}).json()

    response = client.patch(
        f"/tasks/{created['id']}", json={"status": "in_progress"}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


def test_eliminar_tarea_existente(client):
    created = client.post("/tasks/", json={"title": "A eliminar"}).json()

    response = client.delete(f"/tasks/{created['id']}")

    assert response.status_code == 204
    assert client.get(f"/tasks/{created['id']}").status_code == 404


# ---------------------------------------------------------------------------
# Bug conocido: GET /tasks/ devuelve siempre lista vacía
# ---------------------------------------------------------------------------

def test_listar_tareas_devuelve_lista_vacia(client):
    # Bug: list_tasks retorna [] en lugar de db.query(Task).all()
    client.post("/tasks/", json={"title": "Primera tarea"})
    client.post("/tasks/", json={"title": "Segunda tarea"})

    response = client.get("/tasks/")

    assert response.status_code == 200
    assert response.json() == []


# ---------------------------------------------------------------------------
# Errores y casos límite
# ---------------------------------------------------------------------------

def test_crear_tarea_sin_campo_titulo(client):
    # Pydantic rechaza el payload si falta el campo obligatorio "title"
    response = client.post("/tasks/", json={})

    assert response.status_code == 422


def test_crear_tarea_titulo_vacio(client):
    # Validación: título debe tener al menos 3 caracteres
    response = client.post("/tasks/", json={"title": ""})

    assert response.status_code == 422
    assert response.json()["detail"] == "El título debe tener al menos 3 caracteres"


def test_crear_tarea_titulo_corto(client):
    # Título menor a 3 caracteres es rechazado
    response = client.post("/tasks/", json={"title": "ab"})

    assert response.status_code == 422
    assert response.json()["detail"] == "El título debe tener al menos 3 caracteres"


def test_crear_tarea_estado_invalido(client):
    # Un valor de status fuera del enum devuelve 422
    response = client.post("/tasks/", json={"title": "Tarea", "status": "invalid"})

    assert response.status_code == 422


def test_obtener_tarea_no_encontrada(client):
    response = client.get("/tasks/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_actualizar_tarea_establecer_done(client):
    # No se permite establecer el estado a "done" directamente vía PATCH
    created = client.post("/tasks/", json={"title": "Tarea"}).json()

    response = client.patch(
        f"/tasks/{created['id']}", json={"status": "done"}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "No se puede establecer el estado a done directamente"


def test_actualizar_tarea_estado_invalido(client):
    created = client.post("/tasks/", json={"title": "Tarea"}).json()

    response = client.patch(
        f"/tasks/{created['id']}", json={"status": "invalid"}
    )

    assert response.status_code == 422


def test_actualizar_tarea_no_encontrada(client):
    response = client.patch("/tasks/9999", json={"title": "Nuevo título"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_eliminar_tarea_no_encontrada(client):
    response = client.delete("/tasks/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"
