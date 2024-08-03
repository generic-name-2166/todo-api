from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Annotated, Optional

from fastapi import Body, Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from psycopg import AsyncConnection

from todo_api.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
    Token,
)
from todo_api.db import (
    create_task,
    create_user,
    db_pool,
    find_permissions,
    find_task,
    get_db_conn,
    read_tasks,
    remove_task,
    remove_user,
    update_task,
    update_user,
)
from todo_api.models import NewTask, NewUser, Permission, Task, User


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
    """Lists task user is creator of or has read permissions for"""
    return await read_tasks(db, user.id)


@app.post("/tasks")
async def post_task(
    user: Annotated[User, Depends(get_current_user)],
    task: NewTask,
    db: AsyncConnection = Depends(get_db_conn),
):
    await create_task(db, user.id, task)


@app.get("/tasks/{task_id}")
async def get_task_by_id(
    user: Annotated[User, Depends(get_current_user)],
    task_id: int,
    db: AsyncConnection = Depends(get_db_conn),
) -> Task:
    result: Optional[Task] = await find_task(db, user.id, task_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return result


@app.put("/tasks/{task_id}")
async def put_task(
    user: Annotated[User, Depends(get_current_user)],
    task_id: int,
    task: NewTask,
    db: AsyncConnection = Depends(get_db_conn),
):
    result: bool = await update_task(db, user.id, task_id, task)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")


@app.delete("/tasks/{task_id}")
async def delete_task(
    user: Annotated[User, Depends(get_current_user)],
    task_id: int,
    db: AsyncConnection = Depends(get_db_conn),
):
    result: bool = await remove_task(db, user.id, task_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")


@app.get("/tasks/{task_id}/permissions")
async def get_task_permissions(
    user: Annotated[User, Depends(get_current_user)],
    task_id: int,
    db: AsyncConnection = Depends(get_db_conn),
) -> list[Permission]:
    result: Optional[list[Permission]] = await find_permissions(db, user.id, task_id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return result


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
    return current_user


@app.post("/user")
async def post_user(user: NewUser, db: AsyncConnection = Depends(get_db_conn)):
    hashed_password: str = get_password_hash(user.password)
    result: bool = await create_user(db, user.username, hashed_password)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That username is taken. Try another",
        )


@app.put("/user")
async def put_user(
    current: Annotated[User, Depends(get_current_user)],
    username: Annotated[str, Body()],
    db: AsyncConnection = Depends(get_db_conn),
):
    """
    Update username of current user

    Logs user out on success
    """
    result: bool = await update_user(db, current.id, username)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="That username is taken. Try another",
        )


@app.delete("/user")
async def delete_user(
    user: Annotated[User, Depends(get_current_user)],
    db: AsyncConnection = Depends(get_db_conn),
):
    """
    Deletes currently logged in user

    Also deletes all tasks they had created
    """
    await remove_user(db, user.id)
