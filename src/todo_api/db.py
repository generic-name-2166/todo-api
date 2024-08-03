from collections.abc import AsyncGenerator
from typing import Any, Optional

from psycopg import AsyncConnection, sql
from psycopg.rows import dict_row, DictRow
from psycopg_pool import AsyncConnectionPool

from todo_api.models import User


def contsruct_uri(user: str, password: str, host: str, port: int, db_name: str) -> str:
    return f"postgres://{user}:{password}@{host}:{port}/{db_name}"


CONNINFO: str = contsruct_uri("postgres", "postgres", "localhost", 5432, "todo_api")
CONN_ARGS: dict[str, Any] = {"row_factory": dict_row}

db_pool = AsyncConnectionPool(conninfo=CONNINFO, open=False, kwargs=CONN_ARGS)


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
    query: sql.Composed = sql.SQL("SELECT create_user({username}, {hashed_password})").format(
        username=username,
        hashed_password=hashed_password
    )
    cursor = await db.execute(query)
    result: Optional[DictRow] = await cursor.fetchone()  # type: ignore  type doesn't see dict_row factory
    return result is not None and result["create_user"]
