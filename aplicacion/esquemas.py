from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from aplicacion.modelos import TaskPriority, TaskStatus


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = Field(default=None, max_length=500)
    status: TaskStatus = TaskStatus.pending
    priority: TaskPriority = TaskPriority.medium


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = Field(default=None, max_length=500)
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None


class TaskCountResponse(BaseModel):
    total: int


class TaskResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    status: TaskStatus
    priority: TaskPriority
    created_at: datetime

    model_config = {"from_attributes": True}
