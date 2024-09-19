from collections.abc import AsyncGenerator, Sequence
from datetime import datetime
import os
from typing import Optional

from sqlalchemy import delete, exists, select, update
from sqlalchemy.engine import Result
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import selectinload

from todo_api.models import DbTag, DbTask, DbUser
from todo_api.schemas import NewTask, Task, User


def contsruct_uri(user: str, password: str, host: str, port: int, db_name: str) -> str:
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{db_name}"


# Coalescing operator in case POSTGRES_HOST is set to an empty string
HOST: str = os.environ.get("POSTGRES_HOST", None) or "localhost"
CONNINFO: str = contsruct_uri("postgres", "postgres", HOST, 5432, "todo_api")

engine = create_async_engine(CONNINFO)
SessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, bind=engine, expire_on_commit=False
)


async def get_db_conn() -> AsyncGenerator[AsyncSession]:
    global SessionLocal
    async with SessionLocal() as session, session.begin():
        yield session


def extract_one[T](row: Result[tuple[T]]) -> Optional[T]:
    res = row.one_or_none()
    if res is None:
        return None
    return res[0]


async def find_user(db: AsyncSession, username: str) -> Optional[User]:
    query = select(DbUser).where(DbUser.username == username)
    result: Optional[DbUser] = await db.scalar(query)
    if result is None:
        return None
    return User(
        id=result.id,
        username=result.username,
        hashed_password=result.hashed_password,
        telegram_id=result.telegram_id,
    )


async def username_exists(db: AsyncSession, username: str) -> bool:
    query = exists().where(DbUser.username == username).select()
    return await db.scalar(query) or False


async def create_user(
    db: AsyncSession, username: str, hashed_password: str, telegram_id: Optional[int]
) -> bool:
    """Returns whether the user can take this username"""
    if await username_exists(db, username):
        return False
    db.add(
        DbUser(
            username=username, hashed_password=hashed_password, telegram_id=telegram_id
        )
    )
    return True


async def update_user(db: AsyncSession, user_id: int, username: str) -> bool:
    """Returns whether the user can take this username"""
    if await username_exists(db, username):
        return False
    query = update(DbUser).where(DbUser.id == user_id).values(username=username)
    await db.execute(query)
    return True


async def remove_user(db: AsyncSession, user_id: int) -> None:
    tasks_query = (
        delete(DbTask).where(DbTask.creator_id == user_id).returning(DbTask.id)
    )
    deleted_tasks: Sequence[int] = (await db.scalars(tasks_query)).all()
    tags_query = delete(DbTag).where(DbTag.task_id.in_(deleted_tasks))
    await db.execute(tags_query)
    query = delete(DbUser).where(DbUser.id == user_id)
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
    db.add_all(tags)


async def create_task(db: AsyncSession, user_id: int, task: NewTask):
    now = datetime.now()
    db_task = DbTask(
        title=task.title,
        contents=task.contents,
        created_at=now,
        last_edited_at=now,
        creator_id=user_id,
    )
    db.add(db_task)
    await db.flush()
    await create_tags(db, db_task.id, task.tags)


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


async def remove_tags(db: AsyncSession, task_id: int) -> None:
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
    await remove_tags(db, task_id)
    await create_tags(db, task_id, task.tags)
    return True


async def remove_task(db: AsyncSession, user_id: int, task_id: int) -> bool:
    """Returns whether user is authorized to delete the task"""
    if not await is_authorized(db, user_id, task_id):
        return False
    await remove_tags(db, task_id)
    query = delete(DbTask).where(DbTask.creator_id == user_id, DbTask.id == task_id)
    await db.execute(query)
    return True


async def find_tasks_by_tag(
    db: AsyncSession, user_id: int, tag_name: str
) -> list[Task]:
    raise NotImplementedError()
