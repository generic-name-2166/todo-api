from collections.abc import AsyncGenerator
from datetime import datetime
import os
from typing import Any, Optional

from psycopg import AsyncConnection, sql
from psycopg.rows import dict_row, DictRow
from psycopg_pool import AsyncConnectionPool
from sqlalchemy import delete, exists, insert, select, update
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import selectinload

from todo_api.models import DbTag, DbTask
from todo_api.schemas import NewTask, Task, User


def contsruct_uri(user: str, password: str, host: str, port: int, db_name: str) -> str:
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db_name}"


# Coalescing operator in case POSTGRES_HOST is set to an empty string
HOST: str = os.environ.get("POSTGRES_HOST", None) or "localhost"
CONNINFO: str = contsruct_uri("postgres", "postgres", HOST, 5432, "todo_api")
CONN_ARGS: dict[str, Any] = {"row_factory": dict_row}

db_pool = AsyncConnectionPool(conninfo=CONNINFO, open=False, kwargs=CONN_ARGS)
engine = create_async_engine(CONNINFO)
SessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
)


async def get_db_conn() -> AsyncGenerator[AsyncSession]:
    global SessionLocal
    async with SessionLocal() as session:
        yield session


def extract_one[T](row: Result[tuple[T]]) -> Optional[T]:
    res = row.one_or_none()
    if res is None:
        return None
    return res[0]


async def find_user(db: AsyncConnection, username: str) -> Optional[User]:
    query: sql.Composed = sql.SQL("SELECT * FROM get_current_user({username})").format(
        username=username
    )
    cursor = await db.execute(query)
    user_data: Optional[DictRow] = await cursor.fetchone()  # type: ignore  type doesn't see dict_row factory
    if user_data is None:
        return None
    return User(
        id=user_data["id"],
        username=user_data["username"],
        hashed_password=user_data["hashed_password"],
    )


async def create_user(db: AsyncConnection, username: str, hashed_password: str) -> bool:
    query: sql.Composed = sql.SQL(
        "SELECT create_user({username}, {hashed_password})"
    ).format(username=username, hashed_password=hashed_password)
    cursor = await db.execute(query)
    result: Optional[DictRow] = await cursor.fetchone()  # type: ignore  type doesn't see dict_row factory
    return result is not None and result["create_user"]


async def update_user(db: AsyncConnection, user_id: int, username: str) -> bool:
    query: sql.Composed = sql.SQL("SELECT update_user({user_id}, {username})").format(
        user_id=user_id, username=username
    )
    cursor = await db.execute(query)
    result: Optional[DictRow] = await cursor.fetchone()  # type: ignore  type doesn't see dict_row factory
    return result is not None and result["update_user"]


async def remove_user(db: AsyncConnection, user_id: int):
    query: sql.Composed = sql.SQL("SELECT remove_user({user_id})").format(
        user_id=user_id
    )
    await db.execute(query)


def form_task(db_task: DbTask) -> Task:
    return Task(
        id=db_task.id,
        creator_id=db_task.creator_id,
        title=db_task.title,
        contents=db_task.contents,
        tags=db_task.tags,
    )


async def read_tasks(db: AsyncSession, user_id: int) -> list[Task]:
    query = (
        select(DbTask)
        .options(selectinload(DbTask.tags))
        .where(DbTask.creator_id == user_id)
    )
    return list(map(form_task, (await db.scalars(query)).all()))


def unform_tag(task_id: int, tag_name: str) -> dict[str, str | int]:
    return {
        "task_id": task_id,
        "name": tag_name,
    }


async def create_tags(db: AsyncSession, task_id: int, tag_names: list[str]) -> None:
    tags = list(map(lambda name: unform_tag(task_id, name), tag_names))
    await db.execute(insert(DbTag), tags)


async def create_task(db: AsyncSession, user_id: int, task: NewTask):
    now = datetime.now()
    task_id: Optional[int] = await db.scalar(
        insert(DbTask).returning(DbTask.id),
        [
            {
                "title": task.title,
                "contents": task.contents,
                "created_at": now,
                "last_edited_at": now,
                "creator_id": user_id,
            }
        ],
    )
    if task_id is None:
        raise BaseException("could not create a new task")
    await create_tags(db, task_id, task.tags)


async def find_task(db: AsyncSession, user_id: int, task_id: int) -> Optional[Task]:
    query = (
        select(DbTask)
        .options(selectinload(DbTask.tags))
        .where(DbTask.id == task_id, DbTask.creator_id == user_id)
    )
    db_task: Optional[DbTask] = await db.scalar(query)
    if db_task is None:
        return None
    return form_task(db_task)


def unform_task(task: NewTask) -> dict[str, str | Optional[str] | datetime]:
    now = datetime.now()
    return {
        "title": task.title,
        "contents": task.contents,
        "last_edited_at": now,
    }


async def delete_tags(db: AsyncSession, task_id: int) -> None:
    query = delete(DbTag).where(DbTag.task_id == task_id)
    await db.execute(query)


async def is_authorized(db: AsyncSession, user_id: int, task_id: int) -> bool:
    query = (
        exists(DbTask)
        .where(DbTask.id == task_id, DbTask.creator_id == user_id)
        .select()
    )
    return await db.scalar(query) or False


async def update_task(
    db: AsyncSession, user_id: int, task_id: int, task: NewTask
) -> bool:
    """Returns whether user is authorized to update the task"""
    if not await is_authorized(db, user_id, task_id):
        return False
    query = (
        update(DbTask)
        .where(DbTask.id == task_id, DbTask.creator_id == user_id)
        .values(**unform_task(task))
    )
    await db.execute(query)
    await delete_tags(db, task_id)
    await create_tags(db, task_id, task.tags)
    return True


async def remove_task(db: AsyncSession, user_id: int, task_id: int) -> bool:
    """Returns whether user is authorized to delete the task"""
    if not await is_authorized(db, user_id, task_id):
        return False
    await delete_tags(db, task_id)
    query = delete(DbTask).where(DbTask.creator_id == user_id, DbTask.id == task_id)
    await db.execute(query)
    return True


async def find_tasks_by_tag(
    db: AsyncSession, user_id: int, tag_name: str
) -> list[Task]:
    raise NotImplementedError()
