from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional
import re

class UserCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    age: Optional[int] = Field(None, ge=1, le=150)
    is_subscribed: Optional[bool] = Field(False)
    
    class Config:
        json_schema_extra = {
            "example": {
                "name": "Alice",
                "email": "alice@example.com",
                "age": 30,
                "is_subscribed": True
            }
        }

class UserResponse(BaseModel):
    name: str
    email: str
    age: Optional[int] = None
    is_subscribed: bool = False

class LoginData(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=4)

class CommonHeaders(BaseModel):
    user_agent: str = Field(..., alias="User-Agent")
    accept_language: str = Field(..., alias="Accept-Language")
    
    @field_validator('accept_language')
    @classmethod
    def validate_accept_language(cls, v: str) -> str:
        pattern = r'^([a-zA-Z]{2,3}(-[a-zA-Z]{2,3})?(;q=[0-1](\.[0-9]+)?)?)(,\s*[a-zA-Z]{2,3}(-[a-zA-Z]{2,3})?(;q=[0-1](\.[0-9]+)?)?)*$'
        if not re.match(pattern, v):
            raise ValueError('Неверный формат Accept-Language')
        return v
    
    class Config:
        populate_by_name = True