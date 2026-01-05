from pydantic import BaseModel, EmailStr
from typing import Optional

class AuthCredentialsCreate(BaseModel):
    username: str
    password: str

class AuthCredentialsList(BaseModel):
    token: str