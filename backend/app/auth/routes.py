from fastapi import APIRouter
from .schema import SignUpModel, SignInModel
from .services import AuthServices
from ..core.dependency import SessionDep

auth_services = AuthServices()
auth_router = APIRouter()


@auth_router.post("/signup", status_code=200)
async def signup(user: SignUpModel, session:SessionDep):
    new_user = await auth_services.signup(user, session)
    return new_user


@auth_router.get("/verify/{token}")
async def verify_user_token(token: str, session: SessionDep):
    token_url_safe = await auth_services.verify_account(token, session)
    return token_url_safe

@auth_router.post("/signin", status_code=200)
async def signin(user: SignInModel, session:SessionDep):
    user = await auth_services.signin(user, session)
    return user

