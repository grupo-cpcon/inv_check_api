from pydantic import BaseModel, EmailStr
from typing import Optional

class ItemCreate(BaseModel):
    description: str
    status: str

class ItemResponse(BaseModel):
    id: str
    description: str
    status: str