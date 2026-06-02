from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from aplicacion.base_de_datos import get_db
from aplicacion.esquemas import TaskCreate, TaskResponse, TaskUpdate
from aplicacion.modelos import Task, TaskStatus

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", response_model=List[TaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    """Obtiene la lista completa de tareas almacenadas."""
    return db.query(Task).all()


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Obtiene una tarea por su identificador."""
    # Buscar tarea por id y devolver 404 si no existe
    if task_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid task id")
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")
    return task


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    """Crea una nueva tarea y la persiste en la base de datos."""
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
    """Actualiza parcialmente una tarea existente."""
    # Buscar tarea por id y devolver 404 si no existe
    if task_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid task id")
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")

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


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def delete_all_tasks(db: Session = Depends(get_db)):
    """Elimina todas las tareas de la base de datos."""
    db.query(Task).delete()
    db.commit()


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Elimina una tarea de la base de datos."""
    # Buscar tarea por id y devolver 404 si no existe
    if task_id <= 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid task id")
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tarea no encontrada")
    db.delete(task)
    db.commit()
