import asyncio
import platform

from todo_api.models import DbBase
from todo_api.db import engine


"""
File to migrate SQLAlchemy models
Delete afterwards
"""


# On Windows, Psycopg is not compatible with the default ProactorEventLoop
# https://www.psycopg.org/psycopg3/docs/advanced/async.html
if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(DbBase.metadata.create_all)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
