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


# --- Tests del campo prioridad ---


def test_create_task_default_priority_is_medium():
    """Verifica que la prioridad por defecto es medium al crear una tarea."""
    response = client.post("/tasks/", json={"title": "Tarea sin prioridad"})
    assert response.status_code == 201
    assert response.json()["priority"] == "medium"


def test_create_task_with_explicit_priority():
    """Verifica que se puede crear una tarea con prioridad explícita."""
    for priority in ("low", "medium", "high"):
        response = client.post(
            "/tasks/", json={"title": f"Tarea {priority}", "priority": priority}
        )
        assert response.status_code == 201
        assert response.json()["priority"] == priority


def test_create_task_with_invalid_priority_returns_422():
    """Verifica que una prioridad inválida devuelve 422."""
    response = client.post(
        "/tasks/", json={"title": "Tarea inválida", "priority": "urgent"}
    )
    assert response.status_code == 422


def test_update_task_priority():
    """Verifica que se puede actualizar la prioridad de una tarea."""
    response = client.post("/tasks/", json={"title": "Tarea para actualizar"})
    task_id = response.json()["id"]
    assert response.json()["priority"] == "medium"

    response = client.patch(f"/tasks/{task_id}", json={"priority": "high"})
    assert response.status_code == 200
    assert response.json()["priority"] == "high"


def test_update_task_invalid_priority_returns_422():
    """Verifica que actualizar con prioridad inválida devuelve 422."""
    response = client.post("/tasks/", json={"title": "Tarea prioridad"})
    task_id = response.json()["id"]

    response = client.patch(f"/tasks/{task_id}", json={"priority": "critical"})
    assert response.status_code == 422


def test_get_task_includes_priority():
    """Verifica que GET /tasks/{id} devuelve el campo prioridad."""
    response = client.post(
        "/tasks/", json={"title": "Tarea con prioridad", "priority": "low"}
    )
    task_id = response.json()["id"]

    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["priority"] == "low"


# --- Tests de cobertura para get_task_or_404, update_task y delete_task ---


def test_get_task_with_invalid_id_returns_400():
    """Verifica que GET /tasks/{id} con id <= 0 devuelve 400."""
    for invalid_id in (0, -1):
        response = client.get(f"/tasks/{invalid_id}")
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid task id"


def test_get_task_not_found_returns_404():
    """Verifica que GET /tasks/{id} con id inexistente devuelve 404."""
    response = client.get("/tasks/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Tarea no encontrada"


def test_update_nonexistent_task_returns_404():
    """Verifica que PATCH /tasks/{id} con id inexistente devuelve 404."""
    response = client.patch(
        "/tasks/99999", json={"title": "Titulo nuevo"}
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_update_task_title_too_short_returns_422():
    """Verifica que PATCH /tasks/{id} con título corto devuelve 422."""
    create_resp = client.post(
        "/tasks/", json={"title": "Tarea para titulo corto"}
    )
    task_id = create_resp.json()["id"]

    response = client.patch(
        f"/tasks/{task_id}", json={"title": "ab"}
    )
    assert response.status_code == 422
    assert response.json()["detail"] == (
        "El título debe tener al menos 3 caracteres"
    )


def test_delete_single_task():
    """Verifica que DELETE /tasks/{id} elimina la tarea y devuelve 204."""
    create_resp = client.post(
        "/tasks/", json={"title": "Tarea para eliminar"}
    )
    task_id = create_resp.json()["id"]

    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 204

    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 404


def test_delete_task_with_invalid_id_returns_400():
    """Verifica que DELETE /tasks/0 devuelve 400."""
    response = client.delete("/tasks/0")
    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid task id"


def test_delete_task_not_found_returns_404():
    """Verifica que DELETE /tasks/99999 devuelve 404."""
    response = client.delete("/tasks/99999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Tarea no encontrada"
