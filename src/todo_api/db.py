from collections.abc import AsyncGenerator
import os
from typing import Any, Optional

from psycopg import AsyncConnection, sql
from psycopg.rows import dict_row, DictRow
from psycopg_pool import AsyncConnectionPool
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from todo_api.schemas import NewPermission, NewTask, Permission, PermType, Task, User


def contsruct_uri(user: str, password: str, host: str, port: int, db_name: str) -> str:
    return f"postgres://{user}:{password}@{host}:{port}/{db_name}"


# Coalescing operator in case POSTGRES_HOST is set to an empty string
HOST: str = os.environ.get("POSTGRES_HOST", None) or "localhost"
CONNINFO: str = contsruct_uri("postgres", "postgres", HOST, 5432, "todo_api")
CONN_ARGS: dict[str, Any] = {"row_factory": dict_row}

db_pool = AsyncConnectionPool(conninfo=CONNINFO, open=False, kwargs=CONN_ARGS)
engine = create_engine(CONNINFO)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


async def get_db_conn() -> AsyncGenerator[AsyncConnection]:
    global db_pool
    async with db_pool.connection() as aconn:
        yield aconn


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


def form_task(info: DictRow) -> Task:
    return Task(
        id=info["id"],
        creator_id=info["creator_id"],
        name=info["name"],
        description=info["description"],
        finished=info["finished"],
    )


async def read_tasks(db: AsyncConnection, user_id: int) -> list[Task]:
    query: sql.Composed = sql.SQL("SELECT * FROM read_tasks({user_id})").format(
        user_id=user_id
    )
    cursor = await db.execute(query)
    task_data: list[DictRow] = await cursor.fetchall()  # type: ignore  type doesn't see dict_row factory
    return list(map(form_task, task_data))


async def create_task(db: AsyncConnection, user_id: int, task: NewTask):
    query: sql.Composed = sql.SQL(
        "SELECT create_task({user_id}, {name}, {description})"
    ).format(user_id=user_id, name=task.name, description=task.description)
    await db.execute(query)


async def find_task(db: AsyncConnection, user_id: int, task_id: int) -> Optional[Task]:
    query: sql.Composed = sql.SQL(
        "SELECT * FROM find_task({user_id}, {task_id})"
    ).format(user_id=user_id, task_id=task_id)
    cursor = await db.execute(query)
    task_data: Optional[DictRow] = await cursor.fetchone()  # type: ignore  type doesn't see dict_row factory
    if task_data is None:
        return None
    return form_task(task_data)


async def update_task(
    db: AsyncConnection, user_id: int, task_id: int, task: NewTask
) -> bool:
    """Returns whether user is authorized to update the task"""
    query: sql.Composed = sql.SQL(
        "SELECT update_task({user_id}, {task_id}, {name}, {description}, {finished})"
    ).format(
        user_id=user_id,
        task_id=task_id,
        name=task.name,
        description=task.description,
        finished=task.finished,
    )
    cursor = await db.execute(query)
    result: Optional[DictRow] = await cursor.fetchone()  # type: ignore  type doesn't see dict_row factory
    return result is not None and result["update_task"]


async def remove_task(db: AsyncConnection, user_id: int, task_id: int) -> bool:
    """Returns whether user is authorized to delete the task"""
    query: sql.Composed = sql.SQL("SELECT remove_task({user_id}, {task_id})").format(
        user_id=user_id, task_id=task_id
    )
    cursor = await db.execute(query)
    result: Optional[DictRow] = await cursor.fetchone()  # type: ignore  type doesn't see dict_row factory
    return result is not None and result["remove_task"]


def form_permission(info: DictRow) -> Permission:
    return Permission(
        task_id=info["task_id"], user_id=info["user_id"], perm_type=info["perm_type"]
    )


async def find_permissions(
    db: AsyncConnection, user_id: int, task_id: int
) -> Optional[list[Permission]]:
    """Returns None if user is not authorized to see permissions"""
    auth_query: sql.Composed = sql.SQL(
        "SELECT find_is_creator({user_id}, {task_id})"
    ).format(user_id=user_id, task_id=task_id)
    cursor = await db.execute(auth_query)
    result: Optional[DictRow] = await cursor.fetchone()  # type: ignore  type doesn't see dict_row factory
    is_creator: bool = result is not None and result["find_is_creator"]

    if not is_creator:
        return None

    query: sql.Composed = sql.SQL(
        "SELECT * FROM find_permissions({user_id}, {task_id})"
    ).format(user_id=user_id, task_id=task_id)
    cursor = await cursor.execute(query)
    perms: list[DictRow] = await cursor.fetchall()  # type: ignore  type doesn't see dict_row factory
    return list(map(form_permission, perms))


async def add_permission(
    db: AsyncConnection, user_id: int, task_id: int, permission: NewPermission
) -> bool:
    """Returns False if the user isn't authorized to add permissions"""
    query: sql.Composed = sql.SQL(
        "SELECT add_permission({user_id}, {task_id}, {recepient_id}, {perm_type})"
    ).format(
        user_id=user_id,
        task_id=task_id,
        recepient_id=permission.recepient_id,
        perm_type=permission.perm_type,
    )
    cursor = await db.execute(query)
    result: Optional[DictRow] = await cursor.fetchone()  # type: ignore  type doesn't see dict_row factory
    return result is not None and result["add_permission"]


async def remove_permission(
    db: AsyncConnection,
    user_id: int,
    task_id: int,
    recepient_id: int,
    perm_type: PermType,
) -> bool:
    """Returns False if the user isn't authorized to add permissions"""
    query: sql.Composed = sql.SQL(
        "SELECT remove_permission({user_id}, {task_id}, {recepient_id}, {perm_type})"
    ).format(
        user_id=user_id,
        task_id=task_id,
        recepient_id=recepient_id,
        perm_type=perm_type,
    )
    cursor = await db.execute(query)
    result: Optional[DictRow] = await cursor.fetchone()  # type: ignore  type doesn't see dict_row factory
    return result is not None and result["remove_permission"]
