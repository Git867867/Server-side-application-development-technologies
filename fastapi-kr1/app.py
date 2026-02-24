from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, FileResponse, HTMLResponse
from fastapi import Request
from typing import List, Optional
import uvicorn


from models import User, UserAge, Feedback, FeedbackValidated

# Задание 1.1 - Создание приложения
application = FastAPI(title="FastAPI Контрольная работа №1")


# Задание 1.4 - Создаем экземпляр пользователя
user_db = User(name="Иван Петров", id=1)

# Задание 2.1 и 2.2 - Хранилище отзывов
feedbacks_db: List[dict] = []


# Задание 1.1 - Корневой маршрут
@application.get("/")
async def root():
    """
    Возвращает приветственное сообщение
    """
    return {"message": "Добро пожаловать в моё приложение FastAPI!"}

# Для проверки автоперезагрузки раскомментируйте эту область:
# @application.get("/")
# async def root():
#     return {"message": "Автоперезагрузка действительно работает"}


# Задание 1.2 - Возврат HTML страницы
@application.get("/html", response_class=HTMLResponse)
async def get_html_page():
    """
    Возвращает HTML страницу из файла index.html
    """
    return FileResponse("index.html")


# Задание 1.3 - POST запрос
@application.post("/calculate")
async def calculate_numbers(num1: float, num2: float):
    """
    Принимает два числа и возвращает их сумму
    Пример: POST /calculate?num1=5&num2=10
    """
    result = num1 + num2
    return {"result": result}


# Другой вариант для задания 1.3 через JSON запроса
@application.post("/calculate/json")
async def calculate_numbers_json(data: dict):
    """
    Принимает JSON с двумя числами и возвращает их сумму
    Пример: {"num1": 5, "num2": 10}
    """
    if "num1" not in data or "num2" not in data:
        raise HTTPException(status_code=400, detail="Необходимо указать num1 и num2")
    
    try:
        num1 = float(data["num1"])
        num2 = float(data["num2"])
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="num1 и num2 должны быть числами")
    
    result = num1 + num2
    return {"result": result}


# Задание 1.4 - GET запрос /users
@application.get("/users")
async def get_user():
    """
    Возвращает данные пользователя из user_db
    """
    return user_db


# Задание 1.5* - POST запрос /user для проверки совершеннолетия
@application.post("/user")
async def check_user_adult(user: UserAge):
    """
    Принимает данные пользователя и определяет, совершеннолетний ли он
    """
    is_adult = user.age >= 18
    
    return {
        "name": user.name,
        "age": user.age,
        "is_adult": is_adult
    }


# Задание 2.1 - POST запрос /feedback
@application.post("/feedback/v1")
async def submit_feedback(feedback: Feedback):
    """
    Принимает отзыв и сохраняет его в хранилище
    """
    feedback_dict = {
        "name": feedback.name,
        "message": feedback.message
    }
    feedbacks_db.append(feedback_dict)
    
    return {
        "message": f"Feedback received. Thank you, {feedback.name}."
    }


# Задание 2.2* - POST запрос /feedback
@application.post("/feedback")
async def submit_feedback_validated(feedback: FeedbackValidated):
    """
    Принимает отзыв с валидацией, сохраняет в хранилище
    Запрещенные слова: крингк, рофл, вайб
    """
    feedback_dict = {
        "name": feedback.name,
        "message": feedback.message
    }
    feedbacks_db.append(feedback_dict)
    
    return {
        "message": f"Спасибо, {feedback.name}! Ваш отзыв сохранён."
    }


# Эндпоинт для просмотра всех отзывов
@application.get("/feedbacks")
async def get_all_feedbacks():
    """
    Возвращает список всех сохраненных отзывов
    """
    return {"feedbacks": feedbacks_db, "total": len(feedbacks_db)}


# Точка входа для запуска приложения
if __name__ == "__main__":
    uvicorn.run("app:application", host="127.0.0.1", port=8000, reload=True)