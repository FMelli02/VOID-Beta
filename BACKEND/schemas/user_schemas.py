from pydantic import BaseModel, EmailStr, Field
from typing import Optional

# ¡NUEVO MODELO! Para estructurar el teléfono
class Phone(BaseModel):
    prefix: str
    number: str

class UserBase(BaseModel):
    email: EmailStr
    name: str
    last_name: str
    phone: Optional[Phone] = None
    role: str = "user" # Default role

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: str = Field(..., alias="_id")

    class Config:
        populate_by_name = True
        arbitrary_types_allowed = True

class Token(BaseModel):
    access_token: str
    token_type: str

class UserUpdateRole(BaseModel):
    role: str