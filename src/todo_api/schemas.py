from typing import Optional

from pydantic import BaseModel, Field


class NewUser(BaseModel):
    username: str
    password: str
    telegram_id: Optional[int] = Field(default=None)


class User(BaseModel):
    id: int
    username: str
    hashed_password: str
    telegram_id: Optional[int] = Field(default=None)

    class Config:
        from_attributes = True


class Tag(BaseModel):
    id: int
    task_id: int
    name: str

    class Config:
        from_attributes = True


class NewTask(BaseModel):
    title: str
    contents: Optional[str] = Field(default=None)
    tags: list[str] = Field(default_factory=list)


class Task(BaseModel):
    id: int
    creator_id: int
    title: str
    contents: Optional[str] = Field(default=None)
    tags: list[str]

    class Config:
        from_attributes = True
