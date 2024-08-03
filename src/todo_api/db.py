from collections.abc import AsyncGenerator
from typing import Any

from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool


def contsruct_uri(user: str, password: str, host: str, port: int, db_name: str) -> str:
    return f"postgres://{user}:{password}@{host}:{port}/{db_name}"


CONNINFO: str = contsruct_uri("postgres", "postgres", "localhost", 5432, "todo_api")
CONN_ARGS: dict[str, Any] = {"row_factory": dict_row}

db_pool = AsyncConnectionPool(conninfo=CONNINFO, open=False, kwargs=CONN_ARGS)


async def get_db_conn() -> AsyncGenerator[AsyncConnection]:
    global db_pool
    async with db_pool.connection() as aconn:
        yield aconn
