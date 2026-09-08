from datetime import timedelta
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.schemas import Token, UserAuthResponse, UserLogin, UserRegister
from app.auth.security import create_access_token, get_password_hash, verify_password
from app.core.config import settings
from app.models.user import User


class AuthService:
    """
    Centralized authentication and user management service.
    """

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        """Fetch user by case-insensitive email address."""
        clean_email = email.strip().lower()
        stmt = select(User).where(User.email == clean_email)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()

    @staticmethod
    async def register_user(db: AsyncSession, user_in: UserRegister) -> User:
        """
        Registers a new user with bcrypt-hashed credentials.
        Raises ValueError if email already exists.
        """
        clean_email = user_in.email.strip().lower()
        existing = await AuthService.get_by_email(db, clean_email)
        if existing:
            raise ValueError(f"Account with email '{clean_email}' already exists.")

        hashed_pwd = get_password_hash(user_in.password)
        db_user = User(
            email=clean_email,
            password_hash=hashed_pwd,
            full_name=user_in.full_name.strip() if user_in.full_name else None,
            is_active=True,
        )
        db.add(db_user)
        await db.commit()
        await db.refresh(db_user)
        return db_user

    @staticmethod
    async def authenticate_user(db: AsyncSession, credentials: UserLogin) -> Optional[User]:
        """
        Authenticates a user against stored password hash and active status.
        """
        user = await AuthService.get_by_email(db, credentials.email)
        if not user:
            return None
        if not verify_password(credentials.password, user.password_hash):
            return None
        if not user.is_active:
            return None
        return user

    @staticmethod
    def create_user_token(user: User) -> Token:
        """
        Generates signed JWT access token for authenticated user.
        """
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            subject=user.id,
            expires_delta=expires_delta,
            extra_claims={"email": user.email},
        )
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=UserAuthResponse.model_validate(user),
        )
