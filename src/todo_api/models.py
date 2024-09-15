from typing import Type, Any

from sqlalchemy import Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base


DbBase: Type[Any] = declarative_base()


class DbUser(DbBase):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    hashed_password = Column(String, nullable=False)
    telegram_id = Column(Integer, nullable=True)

    tasks = relationship("DbTask", back_populates="owner")


class DbTag(DbBase):
    __tablename__ = "tags"

    task_id = Column(Integer, ForeignKey("task.id"), nullable=False)
    name = Column(String, nullable=False)

    task = relationship("DbTask", back_populates="tags")


class DbTask(DbBase):
    __tablename__ = "task"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    contents = Column(Text, nullable=False)
    owner_id = Column(Integer, ForeignKey("user.id"), nullable=False)

    owner = relationship("DbUser", back_populates="tasks")
    tags = relationship("DbTag", back_populates="task")
