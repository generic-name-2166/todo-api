from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from enum import StrEnum
from typing import Annotated, Optional

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from psycopg import AsyncConnection
from pydantic import BaseModel, Field

from todo_api.db import db_pool, get_db_conn


type FakeUserInfo = dict[str, str]
type FakeDb = dict[str, FakeUserInfo]


# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "4a29d888ad4b04b6a627fd650ae1126beecd2b36771e1c1b835b35a318d20300"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


fake_users_db: FakeDb = {
    "johndoe": {
        "username": "johndoe",
        "hashed_password": "$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW",
    }
}


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    id: int
    username: str
    hashed_password: str


class NewUser(BaseModel):
    username: str
    password: str


class NewTask(BaseModel):
    name: str
    description: Optional[str] = Field(default=None)


class Task(BaseModel):
    id: int
    creator_id: int
    name: str
    description: Optional[str] = Field(default=None)
    finished: bool


class PermType(StrEnum):
    Read = "read"
    Update = "update"


class Permission(BaseModel):
    task_id: int
    recepient_id: int
    perm_type: PermType


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    try:
        await db_pool.open()
        yield
    finally:
        await db_pool.close()


app = FastAPI(lifespan=lifespan)  # type: ignore


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def get_user(db: FakeDb, username: str) -> Optional[User]:
    if username in db:
        user_dict = db[username]
        return User(id=0, **user_dict)


def authenticate_user(fake_db: FakeDb, username: str, password: str) -> Optional[User]:
    user: Optional[User] = get_user(fake_db, username)
    if user is None:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(
    data: dict[str, str], expires_delta: Optional[timedelta] = None
) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire: datetime = datetime.now(timezone.utc) + expires_delta
    else:
        expire: datetime = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode = to_encode | {"exp": expire}
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)  # type: ignore
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  # type: ignore
        username: Optional[str] = payload.get("sub")
        if username is None:
            raise credentials_exception
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(fake_users_db, username=username)
    if user is None:
        raise credentials_exception
    return user


@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(fake_users_db, form_data.username, form_data.password)
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
async def add_task(
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
async def read_user(
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
