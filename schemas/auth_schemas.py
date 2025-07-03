from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime
from models import SubscriptionTier

class UserCreate(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=6)

class UserLogin(BaseModel):
    username: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True

class SubscriptionResponse(BaseModel):
    id: int
    tier: SubscriptionTier
    is_active: bool
    expires_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserWithSubscription(UserResponse):
    subscription: Optional[SubscriptionResponse]

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    subscription: Optional[SubscriptionResponse]
