from fastapi import APIRouter
from app.modules.auth.auth_schema import AuthCredentialsCreate, AuthCredentialsList
from app.modules.auth.auth_service import AuthService
from app.core.decorators.auth_decorator import no_auth

router = APIRouter(prefix="/auth", tags=["Auth"])
auth_service = AuthService()

@no_auth
@router.post("/login", response_model=AuthCredentialsList)
async def login(credentials: AuthCredentialsCreate):
    token = await auth_service.authenticate(
        username=credentials.username,
        password=credentials.password
    )
    return AuthCredentialsList(token=token)