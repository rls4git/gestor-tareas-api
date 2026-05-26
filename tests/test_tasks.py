from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from aplicacion.base_de_datos import Base, get_db
from aplicacion.principal import app

# Base SQLite en memoria con StaticPool para compartir la conexión entre hilos
# y mantener el estado entre requests dentro del mismo test run.
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_module():
    Base.metadata.create_all(bind=engine)


def teardown_module():
    Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_task(title: str = "Tarea de prueba", description: str | None = None) -> dict:
    payload = {"title": title}
    if description is not None:
        payload["description"] = description
    response = client.post("/tasks/", json=payload)
    assert response.status_code == 201, response.text
    return response.json()


# ---------------------------------------------------------------------------
# GET /tasks/{task_id}
# ---------------------------------------------------------------------------

def test_get_task_existente_devuelve_200_y_payload():
    created = _create_task(title="Leer libro")
    response = client.get(f"/tasks/{created['id']}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["title"] == "Leer libro"


def test_get_task_inexistente_devuelve_404():
    response = client.get("/tasks/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


# ---------------------------------------------------------------------------
# PATCH /tasks/{task_id}
# ---------------------------------------------------------------------------

def test_patch_task_existente_actualiza_campos():
    created = _create_task(title="Original", description="vieja")
    response = client.patch(
        f"/tasks/{created['id']}",
        json={"title": "Nuevo titulo"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Nuevo titulo"
    # description no se envia -> debe permanecer
    assert body["description"] == "vieja"


def test_patch_task_inexistente_devuelve_404():
    response = client.patch("/tasks/999999", json={"title": "x"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


# ---------------------------------------------------------------------------
# DELETE /tasks/{task_id}
# ---------------------------------------------------------------------------

def test_delete_task_existente_devuelve_204_y_borra():
    created = _create_task(title="A borrar")
    response = client.delete(f"/tasks/{created['id']}")
    assert response.status_code == 204
    assert response.content == b""

    # Confirmamos que ya no existe
    follow_up = client.get(f"/tasks/{created['id']}")
    assert follow_up.status_code == 404


def test_delete_task_inexistente_devuelve_404():
    response = client.delete("/tasks/999999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


# ---------------------------------------------------------------------------
# GET /tasks/
# ---------------------------------------------------------------------------

def test_list_tasks_devuelve_lista():
    response = client.get("/tasks/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


# ---------------------------------------------------------------------------
# Regresion: el helper get_task_or_404 se aplica de forma consistente
# en los tres endpoints que reciben {task_id}.
# ---------------------------------------------------------------------------

def test_404_consistente_en_get_patch_delete():
    missing_id = 424242
    get_resp = client.get(f"/tasks/{missing_id}")
    patch_resp = client.patch(f"/tasks/{missing_id}", json={"title": "x"})
    delete_resp = client.delete(f"/tasks/{missing_id}")

    for resp in (get_resp, patch_resp, delete_resp):
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Task not found"
