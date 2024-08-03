from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from psycopg import AsyncConnection

from todo_api.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    get_current_user,
    Token,
)
from todo_api.db import db_pool, get_db_conn
from todo_api.models import NewTask, NewUser, User, Task, Permission


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        await db_pool.open()
        yield
    finally:
        await db_pool.close()


app = FastAPI(lifespan=lifespan)  # type: ignore


@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncConnection = Depends(get_db_conn),
) -> Token:
    user = await authenticate_user(db, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get("/tasks")
async def get_tasks(
    user: Annotated[User, Depends(get_current_user)],
    db: AsyncConnection = Depends(get_db_conn),
) -> list[Task]:
    # TODO
    return []


@app.post("/tasks")
async def post_task(
    user: Annotated[User, Depends(get_current_user)],
    task: Task,
    db: AsyncConnection = Depends(get_db_conn),
) -> int:
    """Returns the id of added task"""
    # TODO
    return 0


@app.get("/tasks/{task_id}")
async def get_task_by_id(
    user: Annotated[User, Depends(get_current_user)],
    task_id: int,
    db: AsyncConnection = Depends(get_db_conn),
) -> Task:
    # TODO
    return Task(id=task_id, creator_id=0, name="TODO", finished=False)


@app.put("/tasks/{task_id}")
async def put_task(
    user: Annotated[User, Depends(get_current_user)],
    task_id: int,
    task: NewTask,
    db: AsyncConnection = Depends(get_db_conn),
):
    # TODO
    pass


@app.delete("/tasks/{task_id}")
async def delete_task(
    user: Annotated[User, Depends(get_current_user)],
    task_id: int,
    db: AsyncConnection = Depends(get_db_conn),
):
    # TODO
    pass


@app.get("/tasks/{task_id}/permissions")
async def get_task_permissions(
    user: Annotated[User, Depends(get_current_user)],
    task_id: int,
    db: AsyncConnection = Depends(get_db_conn),
) -> list[Permission]:
    # TODO
    return []


@app.post("/tasks/{task_id}/permissions")
async def post_task_permissions(
    user: Annotated[User, Depends(get_current_user)],
    task_id: int,
    perm: Permission,
    db: AsyncConnection = Depends(get_db_conn),
):
    # TODO
    pass


@app.delete("/tasks/{task_id}/permissions")
async def delete_task_permissions(
    user: Annotated[User, Depends(get_current_user)],
    task_id: int,
    perm: Permission,
    db: AsyncConnection = Depends(get_db_conn),
):
    # TODO
    pass


@app.get("/user")  # response_model=User)
async def get_user(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    # SELECT * FROM get_current_user('john_doe');
    return current_user


@app.post("/user")
async def post_user(user: NewUser):
    # TODO
    # TODO check if user with this username already exists
    pass


@app.put("/user")
async def put_user(current: Annotated[User, Depends(get_current_user)], user: NewUser):
    # TODO
    # TODO check if user with this username already exists
    pass


@app.delete("/user")
async def delete_user(user: Annotated[User, Depends(get_current_user)]):
    # TODO
    # TODO delete all tasks user created
    pass
