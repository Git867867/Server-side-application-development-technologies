import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict

from fastapi import Depends, FastAPI, HTTPException, status, Request
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials, HTTPBearer, OAuth2PasswordBearer
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from dotenv import load_dotenv

load_dotenv()

#Конфигурация
MODE = os.getenv("MODE", "DEV")
DOCS_USER = os.getenv("DOCS_USER", "admin")
DOCS_PASSWORD = os.getenv("DOCS_PASSWORD", "secret")

SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

app = FastAPI(
    docs_url=None if MODE == "PROD" else "/docs_protected",
    redoc_url=None,
    openapi_url=None if MODE == "PROD" else "/openapi_protected",
)

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

security_basic = HTTPBasic()
security_bearer = HTTPBearer()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory базы данных
fake_users_db: Dict[str, dict] = {}
todos_db: Dict[int, dict] = {}
todo_counter = 1

# Роли пользователей
user_roles: Dict[str, str] = {}

class UserBase(BaseModel):
    username: str

class User(UserBase):
    password: str

class UserInDB(UserBase):
    hashed_password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class TodoCreate(BaseModel):
    title: str
    description: str

class TodoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    completed: Optional[bool] = None

class Todo(TodoCreate):
    id: int
    completed: bool = False

#Вспомогательные функции
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# Задание 6.1 и 6.2 -----------------
def auth_user(credentials: HTTPBasicCredentials = Depends(security_basic)):
    username = credentials.username
    password = credentials.password

    if username not in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    user = fake_users_db[username]
    if not secrets.compare_digest(username, user["username"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    if not verify_password(password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    return user

@app.post("/register")
@limiter.limit("1/minute")
async def register(request: Request, user: User):
    if user.username in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists"
        )
    
    hashed = get_password_hash(user.password)
    fake_users_db[user.username] = {
        "username": user.username,
        "hashed_password": hashed
    }
    # По умолчанию роль "guest"
    user_roles[user.username] = "guest"
    
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={"message": "New user created"}
    )

@app.get("/login")
async def login(user: dict = Depends(auth_user)):
    return {"message": f"Welcome, {user['username']}!"}

#Задание 6.3 ------------
def docs_auth(credentials: HTTPBasicCredentials = Depends(security_basic)):
    if not secrets.compare_digest(credentials.username, DOCS_USER):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Basic"},
        )
    if not secrets.compare_digest(credentials.password, DOCS_PASSWORD):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            headers={"WWW-Authenticate": "Basic"},
        )
    return True

if MODE == "DEV":
    @app.get("/docs", include_in_schema=False)
    async def custom_docs(auth: bool = Depends(docs_auth)):
        return get_swagger_ui_html(openapi_url="/openapi.json", title="API Docs")

    @app.get("/openapi.json", include_in_schema=False)
    async def custom_openapi(auth: bool = Depends(docs_auth)):
        return JSONResponse(get_openapi(title="API", version="1.0.0", routes=app.routes))

    @app.get("/redoc", include_in_schema=False)
    async def custom_redoc():
        raise HTTPException(status_code=404, detail="Not Found")

elif MODE == "PROD":
    @app.get("/docs", include_in_schema=False)
    async def no_docs():
        raise HTTPException(status_code=404, detail="Not Found")

    @app.get("/openapi.json", include_in_schema=False)
    async def no_openapi():
        raise HTTPException(status_code=404, detail="Not Found")

    @app.get("/redoc", include_in_schema=False)
    async def no_redoc():
        raise HTTPException(status_code=404, detail="Not Found")

#Задание 6.4 и 6.5 -------------------
@app.post("/login_jwt")
@limiter.limit("5/minute")
async def login_jwt(request: Request, user: User):
    if user.username not in fake_users_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    db_user = fake_users_db[user.username]
    if not secrets.compare_digest(user.username, db_user["username"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization failed"
        )
    
    if not verify_password(user.password, db_user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization failed"
        )
    
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    return {"access_token": access_token, "token_type": "bearer"}

async def get_current_user(token: str = Depends(security_bearer)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    
    if token_data.username not in fake_users_db:
        raise credentials_exception
    
    return fake_users_db[token_data.username]

@app.get("/protected_resource")
async def protected_resource(current_user: dict = Depends(get_current_user)):
    return {"message": "Access granted"}

#Задание 7.1----------
def require_role(required_roles: list):
    async def role_checker(current_user: dict = Depends(get_current_user)):
        username = current_user["username"]
        role = user_roles.get(username, "guest")
        if role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' not authorized"
            )
        return current_user
    return role_checker

@app.post("/admin/create")
async def admin_create(current_user: dict = Depends(require_role(["admin"]))):
    return {"message": "Admin can create resources"}

@app.get("/user/read")
async def user_read(current_user: dict = Depends(require_role(["admin", "user"]))):
    return {"message": "User can read resources"}

@app.put("/user/update")
async def user_update(current_user: dict = Depends(require_role(["admin", "user"]))):
    return {"message": "User can update resources"}

@app.get("/guest/read")
async def guest_read(current_user: dict = Depends(require_role(["admin", "user", "guest"]))):
    return {"message": "Guest can only read limited resources"}

@app.post("/set_role")
async def set_role(username: str, role: str):
    if username not in fake_users_db:
        raise HTTPException(status_code=404, detail="User not found")
    if role not in ["admin", "user", "guest"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    user_roles[username] = role
    return {"message": f"Role '{role}' set for user '{username}'"}

#Задание 8.1 и 8.2

@app.post("/todos", status_code=201)
async def create_todo(todo: TodoCreate):
    global todo_counter
    new_todo = {
        "id": todo_counter,
        "title": todo.title,
        "description": todo.description,
        "completed": False
    }
    todos_db[todo_counter] = new_todo
    todo_counter += 1
    return new_todo

@app.get("/todos/{todo_id}")
async def get_todo(todo_id: int):
    if todo_id not in todos_db:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todos_db[todo_id]

@app.put("/todos/{todo_id}")
async def update_todo(todo_id: int, todo_update: TodoUpdate):
    if todo_id not in todos_db:
        raise HTTPException(status_code=404, detail="Todo not found")
    
    todo = todos_db[todo_id]
    if todo_update.title is not None:
        todo["title"] = todo_update.title
    if todo_update.description is not None:
        todo["description"] = todo_update.description
    if todo_update.completed is not None:
        todo["completed"] = todo_update.completed
    
    return todo

@app.delete("/todos/{todo_id}")
async def delete_todo(todo_id: int):
    if todo_id not in todos_db:
        raise HTTPException(status_code=404, detail="Todo not found")
    del todos_db[todo_id]
    return {"message": "Todo deleted successfully"}

# Запуск -----------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)