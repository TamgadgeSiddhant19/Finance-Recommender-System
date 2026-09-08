from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.schemas import Token, UserAuthResponse, UserLogin, UserRegister
from app.auth.service import AuthService
from app.database.session import get_db
from app.models.user import User

router = APIRouter()


@router.post(
    "/auth/register",
    response_model=Token,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account and obtain initial JWT session",
)
async def register(
    user_in: UserRegister,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Register a new user account with secure bcrypt hashing,
    store user in Neon database, and return a signed JWT access token.
    """
    try:
        user = await AuthService.register_user(db=db, user_in=user_in)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    return AuthService.create_user_token(user)


@router.post(
    "/auth/login",
    response_model=Token,
    summary="Authenticate with email and password to receive a JWT session token",
)
async def login(
    credentials: UserLogin,
    db: AsyncSession = Depends(get_db),
) -> Token:
    """
    Authenticate user credentials, verify bcrypt hash against Neon database,
    and issue a signed JWT access token.
    """
    user = await AuthService.authenticate_user(db=db, credentials=credentials)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AuthService.create_user_token(user)


@router.get(
    "/auth/me",
    response_model=UserAuthResponse,
    summary="Get profile of currently authenticated user",
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Returns identity and status of the current user parsed from JWT Bearer token.
    """
    return current_user


@router.post(
    "/auth/logout",
    summary="Log out client session",
)
async def logout() -> dict:
    """
    Stateless JWT logout endpoint. Informs the client to remove the stored token.
    """
    return {
        "status": "success",
        "message": "Successfully logged out. Please discard your authentication token.",
    }
