from fastapi import FastAPI, HTTPException, Request, Response, status, Depends
import time
import uuid
from datetime import datetime
from typing import Optional
import uvicorn

from models import UserCreate, UserResponse, LoginData, CommonHeaders
from products import sample_products, products_dict
from auth import SessionManager, users_db, TEST_CREDENTIALS

app = FastAPI(
    title="Контрольная работа №2",
    description="FastAPI приложение для контрольной работы",
    version="1.0.0"
)

# Задание 3.1
@app.post("/create_user", 
          response_model=UserResponse,
          status_code=status.HTTP_201_CREATED,
          tags=["Задание 3.1"])
async def create_user(user: UserCreate):
    return UserResponse(
        name=user.name,
        email=user.email,
        age=user.age,
        is_subscribed=user.is_subscribed
    )

# Задание 3.2
@app.get("/product/{product_id}", tags=["Задание 3.2"])
async def get_product(product_id: int):
    product = products_dict.get(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Продукт с ID {product_id} не найден"
        )
    return product

@app.get("/products/search", tags=["Задание 3.2"])
async def search_products(
    keyword: str,
    category: Optional[str] = None,
    limit: int = 10
):
    results = []
    for product in sample_products:
        if keyword.lower() in product["name"].lower():
            if category and product["category"].lower() != category.lower():
                continue
            results.append(product)
    return results[:limit]

# Задание 5.1
@app.post("/login", tags=["Задания 5.x"])
async def login(login_data: LoginData, response: Response):
    if login_data.username not in TEST_CREDENTIALS or \
       TEST_CREDENTIALS[login_data.username] != login_data.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль"
        )
    
    if login_data.username in users_db:
        user_id = users_db[login_data.username]["user_id"]
    else:
        user_id = str(uuid.uuid4())
    
    current_time = int(time.time())
    session_token = SessionManager.create_session_token(user_id, current_time)
    
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        max_age=300,
        secure=False,
        samesite="lax"
    )
    
    return {"message": "Успешный вход", "user_id": user_id}

# Задания 5.2 и 5.3
@app.get("/profile", tags=["Задания 5.x"])
async def get_profile(request: Request, response: Response):
    session_token = request.cookies.get("session_token")
    if not session_token:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"message": "Unauthorized"}
    
    user_id, timestamp = SessionManager.verify_session_token(session_token)
    if not user_id or not timestamp:
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"message": "Invalid session"}
    
    if SessionManager.check_session_expired(timestamp, max_age=300):
        response.status_code = status.HTTP_401_UNAUTHORIZED
        return {"message": "Session expired"}
    
    if SessionManager.should_refresh_session(timestamp, min_refresh=180, max_age=300):
        new_timestamp = int(time.time())
        new_token = SessionManager.create_session_token(user_id, new_timestamp)
        response.set_cookie(
            key="session_token",
            value=new_token,
            httponly=True,
            max_age=300,
            secure=False,
            samesite="lax"
        )
    
    user_profile = None
    for user_data in users_db.values():
        if user_data["user_id"] == user_id:
            user_profile = user_data["profile"]
            break
    
    if not user_profile:
        user_profile = {
            "username": "test_user",
            "full_name": "Test User",
            "email": "test@example.com"
        }
    
    return user_profile

# Задание 5.4
@app.get("/headers", tags=["Задание 5.4"])
async def get_headers(headers: CommonHeaders = Depends()):
    return {
        "User-Agent": headers.user_agent,
        "Accept-Language": headers.accept_language
    }

@app.get("/info", tags=["Задание 5.4"])
async def get_info(response: Response, headers: CommonHeaders = Depends()):
    server_time = datetime.now().isoformat()
    response.headers["X-Server-Time"] = server_time
    
    return {
        "message": "Добро пожаловать! Ваши заголовки успешно обработаны.",
        "headers": {
            "User-Agent": headers.user_agent,
            "Accept-Language": headers.accept_language
        }
    }

# Дополнительные маршруты
@app.get("/session-status", tags=["Задания 5.x"])
async def session_status(request: Request):
    session_token = request.cookies.get("session_token")
    if not session_token:
        return {"authenticated": False, "reason": "No session token"}
    
    user_id, timestamp = SessionManager.verify_session_token(session_token)
    if not user_id:
        return {"authenticated": False, "reason": "Invalid signature"}
    
    current_time = int(time.time())
    elapsed = current_time - timestamp
    
    return {
        "authenticated": True,
        "user_id": user_id[:8] + "...",
        "session_age_seconds": elapsed,
        "session_expired": elapsed > 300,
        "time_until_expiry": max(0, 300 - elapsed),
        "should_refresh": SessionManager.should_refresh_session(timestamp)
    }

@app.post("/logout", tags=["Задания 5.x"])
async def logout(response: Response):
    response.delete_cookie("session_token")
    return {"message": "Успешный выход"}

if __name__ == "__main__":
    print("Запуск FastAPI приложения...")
    print("Документация: http://localhost:8000/docs")
    print("Нажмите Ctrl+C для остановки")
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )