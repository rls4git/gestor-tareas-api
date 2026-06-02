from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from aplicacion.base_de_datos import Base, get_db
from aplicacion.principal import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_tareas.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
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


def test_create_task_title_too_short_returns_422():
    response = client.post("/tasks/", json={"title": "ab"})
    assert response.status_code == 422


def test_update_done_task_returns_409():
    response = client.post("/tasks/", json={"title": "Tarea para completar"})
    assert response.status_code == 201
    task_id = response.json()["id"]

    client.patch(f"/tasks/{task_id}", json={"status": "done"})

    response = client.patch(f"/tasks/{task_id}", json={"title": "Nuevo título"})
    assert response.status_code == 409


def test_delete_all_tasks_clears_database():
    """Verifica que DELETE /tasks/ elimina todas las tareas."""
    # Crear varias tareas
    client.post("/tasks/", json={"title": "Tarea uno"})
    client.post("/tasks/", json={"title": "Tarea dos"})
    client.post("/tasks/", json={"title": "Tarea tres"})

    # Confirmar que existen tareas
    response = client.get("/tasks/")
    assert response.status_code == 200
    assert len(response.json()) > 0

    # Eliminar todas
    response = client.delete("/tasks/")
    assert response.status_code == 204

    # Verificar que la lista está vacía
    response = client.get("/tasks/")
    assert response.status_code == 200
    assert response.json() == []


def test_delete_all_tasks_on_empty_database_returns_204():
    """Verifica que DELETE /tasks/ devuelve 204 incluso sin tareas."""
    # Asegurar que no hay tareas (ya se eliminaron en el test anterior)
    response = client.delete("/tasks/")
    assert response.status_code == 204

    response = client.get("/tasks/")
    assert response.status_code == 200
    assert response.json() == []


def test_create_task_with_categoria():
    """Verifica que se puede crear una tarea con categoría."""
    response = client.post(
        "/tasks/",
        json={"title": "Tarea con categoría", "categoria": "trabajo"}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["categoria"] == "trabajo"


def test_create_task_without_categoria():
    """Verifica que se puede crear una tarea sin categoría (campo opcional)."""
    response = client.post("/tasks/", json={"title": "Tarea sin categoría"})
    assert response.status_code == 201
    data = response.json()
    assert data["categoria"] is None


def test_update_task_categoria():
    """Verifica que se puede actualizar la categoría de una tarea."""
    response = client.post("/tasks/", json={"title": "Tarea para actualizar"})
    assert response.status_code == 201
    task_id = response.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}",
        json={"categoria": "personal"}
    )
    assert response.status_code == 200
    assert response.json()["categoria"] == "personal"


def test_categoria_in_task_response():
    """Verifica que la categoría aparece en la respuesta de obtener tarea."""
    response = client.post(
        "/tasks/",
        json={"title": "Tarea respuesta", "categoria": "urgente"}
    )
    assert response.status_code == 201
    task_id = response.json()["id"]

    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    data = response.json()
    assert "categoria" in data
    assert data["categoria"] == "urgente"
