import uuid
import time
import hashlib
import hmac
from itsdangerous import URLSafeTimedSerializer, BadSignature

SECRET_KEY = "your-secret-key-here-change-in-production"
serializer = URLSafeTimedSerializer(SECRET_KEY)

users_db = {
    "user123": {
        "password": "password123",
        "user_id": str(uuid.uuid4()),
        "profile": {
            "username": "user123",
            "full_name": "Test User",
            "email": "user@example.com"
        }
    }
}

class SessionManager:
    @staticmethod
    def create_session_token(user_id: str, timestamp: int = None) -> str:
        """Формат: <user_id>.<signature> (с timestamp внутри подписи)"""
        if timestamp is None:
            timestamp = int(time.time())
        
        # Подписываем user_id + timestamp
        data = f"{user_id}.{timestamp}"
        signature = serializer.dumps(data)
        
        return f"{user_id}.{signature}"
    
    @staticmethod
    def verify_session_token(token: str) -> tuple:
        try:
            parts = token.split('.')
            if len(parts) != 2:  # Должно быть 2 части: user_id.signature
                return None, None
            
            user_id, signature = parts
            
            # Проверка подписи и извлечение timestamp
            data = serializer.loads(signature, max_age=300)
            expected_user_id, timestamp = data.split('.')
            
            if user_id != expected_user_id:
                return None, None
                
            return user_id, int(timestamp)
                
        except (ValueError, IndexError, BadSignature, AttributeError):
            return None, None
    
    @staticmethod
    def check_session_expired(timestamp: int, max_age: int = 300) -> bool:
        current_time = int(time.time())
        return (current_time - timestamp) > max_age
    
    @staticmethod
    def should_refresh_session(timestamp: int, min_refresh: int = 180, max_age: int = 300) -> bool:
        current_time = int(time.time())
        elapsed = current_time - timestamp
        return min_refresh <= elapsed < max_age

TEST_CREDENTIALS = {
    "user123": "password123"
}