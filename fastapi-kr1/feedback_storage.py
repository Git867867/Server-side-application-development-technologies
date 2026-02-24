from typing import List, Dict, Any

class FeedbackStorage:
    """Класс для управления хранилищем отзывов"""
    
    def __init__(self):
        self.feedbacks: List[Dict[str, Any]] = []
    
    def add_feedback(self, name: str, message: str) -> Dict[str, Any]:
        """Добавляет новый отзыв в хранилище"""
        feedback = {
            "name": name,
            "message": message
        }
        self.feedbacks.append(feedback)
        return feedback
    
    def get_all_feedbacks(self) -> List[Dict[str, Any]]:
        """Возвращает все отзывы"""
        return self.feedbacks
    
    def clear(self):
        """Очищает хранилище"""
        self.feedbacks.clear()

# Создание глобального экземпляра хранилища
storage = FeedbackStorage()