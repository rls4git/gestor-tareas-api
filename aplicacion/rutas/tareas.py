from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from aplicacion.base_de_datos import get_db
from aplicacion.esquemas import TaskCreate, TaskResponse, TaskUpdate
from aplicacion.modelos import Task, TaskStatus

router = APIRouter(prefix="/tasks", tags=["tasks"])


def get_task_or_404(task_id: int, db: Session = Depends(get_db)) -> Task:
    """Obtiene una tarea por id o lanza 404.

    Dependencia compartida que centraliza la validación del identificador
    y la búsqueda en base de datos.

    Args:
        task_id (int): Identificador numérico de la tarea.
        db (Session): Sesión de base de datos inyectada por FastAPI.

    Returns:
        Task: La instancia ORM de la tarea encontrada.

    Raises:
        HTTPException: 400 si el id es menor o igual a cero.
        HTTPException: 404 si no existe una tarea con el id indicado.
    """
    if task_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid task id")
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.get("/", response_model=List[TaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    """Obtiene la lista completa de tareas almacenadas.

    Args:
        db (Session): Sesión de base de datos inyectada por FastAPI.

    Returns:
        List[TaskResponse]: Lista con todas las tareas existentes.
    """
    return []


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task: Task = Depends(get_task_or_404)):
    """Obtiene una tarea por su identificador.

    Args:
        task (Task): Tarea resuelta por la dependencia get_task_or_404.

    Returns:
        TaskResponse: La tarea correspondiente al identificador.

    Raises:
        HTTPException: 400 si el id es inválido.
        HTTPException: 404 si no existe una tarea con el id indicado.
    """
    return task


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    """Crea una nueva tarea y la persiste en la base de datos.

    Args:
        payload (TaskCreate): Datos de la tarea a crear.
        db (Session): Sesión de base de datos inyectada por FastAPI.

    Returns:
        TaskResponse: La tarea recién creada con su id y fecha asignados.

    Raises:
        HTTPException: 422 si el título tiene menos de 3 caracteres.
    """
    if len(payload.title) < 3:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El título debe tener al menos 3 caracteres",
        )
    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    """Actualiza parcialmente una tarea existente.

    Solo modifica los campos incluidos en el cuerpo de la petición.

    Args:
        task_id (int): Identificador único de la tarea a actualizar.
        payload (TaskUpdate): Campos a modificar.
        db (Session): Sesión de base de datos inyectada por FastAPI.

    Returns:
        TaskResponse: La tarea con los campos actualizados.

    Raises:
        HTTPException: 404 si no existe una tarea con el id indicado.
        HTTPException: 400 si se intenta establecer el estado a done.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    if payload.title is not None and len(payload.title) < 3:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El título debe tener al menos 3 caracteres",
        )

    if payload.status == TaskStatus.done:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede establecer el estado a done directamente",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task: Task = Depends(get_task_or_404),
    db: Session = Depends(get_db),
):
    """Elimina una tarea de la base de datos.

    Args:
        task (Task): Tarea resuelta por la dependencia get_task_or_404.
        db (Session): Sesión de base de datos inyectada por FastAPI.

    Returns:
        None: Respuesta vacía con código 204.

    Raises:
        HTTPException: 400 si el id es inválido.
        HTTPException: 404 si no existe una tarea con el id indicado.
    """
    db.delete(task)
    db.commit()
