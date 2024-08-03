from enum import StrEnum
from typing import Optional

from pydantic import BaseModel, Field


class NewUser(BaseModel):
    username: str
    password: str


class User(BaseModel):
    id: int
    username: str
    hashed_password: str


class NewTask(BaseModel):
    name: str
    description: Optional[str] = Field(default=None)


class Task(BaseModel):
    id: int
    creator_id: int
    name: str
    description: Optional[str] = Field(default=None)
    finished: bool


class PermType(StrEnum):
    Read = "read"
    Update = "update"


class Permission(BaseModel):
    task_id: int
    recepient_id: int
    perm_type: PermType
