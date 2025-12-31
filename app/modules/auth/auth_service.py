import httpx
from fastapi import HTTPException, status
from dotenv import load_dotenv
import os

load_dotenv()  

class AuthService:          
    def __init__(self):
        self.auth_provide_url = os.getenv("LEGACY_AUTH_PROVIDE_URL")
        self.auth_validate_url = os.getenv("LEGACY_AUTH_VALIDATE_URL")

    async def authenticate(self, username: str, password: str) -> str:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.auth_provide_url,
                    json={"username": username, "password": password},
                    timeout=60
                )
                response.raise_for_status()
                data = response.json()
                token = data.get("token")
                if not token:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Token not returned by the authentication server."
                    )
                return token
            except httpx.HTTPStatusError as e:
                raise HTTPException(
                    status_code=e.response.status_code,
                    detail=f"Authentication server error: {e.response.text}"
                )
            except httpx.RequestError as e:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Error connecting to the authentication server: {str(e)}"
                )

    async def validate_token(token: str) -> bool:
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    self.auth_validate_url,
                    json={"token": token},
                    timeout=60
                )
                return response.status_code == 200
            except Exception:
                return False
