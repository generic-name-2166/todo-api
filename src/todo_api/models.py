from datetime import datetime

from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class DbBase(DeclarativeBase):
    pass


class DbUser(DbBase):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]
    hashed_password: Mapped[str]
    telegram_id = mapped_column(Integer, nullable=True)

    tasks = relationship("DbTask", back_populates="creator")


class DbTag(DbBase):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True)
    task_id = mapped_column(Integer, ForeignKey("task.id"), nullable=False)
    name: Mapped[str]

    task = relationship("DbTask", back_populates="tags")


class DbTask(DbBase):
    __tablename__ = "task"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str]
    contents: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime]
    last_edited_at: Mapped[datetime]
    creator_id = mapped_column(Integer, ForeignKey("user.id"), nullable=False)

    creator = relationship("DbUser", back_populates="tasks")
    tags = relationship("DbTag", back_populates="task")
