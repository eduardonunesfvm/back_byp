from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core import security
from app.core.config import settings
from app.core.exceptions import (
    EmailAlreadyRegistered,
    InvalidCredentials,
    InvalidToken,
    NotFound,
    TokenExpired,
    UsernameAlreadyRegistered,
)
from app.models.user import User
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.user_repository import UserRepository
from app.schemas.user import TokenPair, UserCreate


class AuthService:
    def __init__(
        self,
        db: Session,
        user_repo: UserRepository | None = None,
        refresh_token_repo: RefreshTokenRepository | None = None,
    ):
        self.db = db
        self.user_repo = user_repo or UserRepository(db)
        self.refresh_token_repo = refresh_token_repo or RefreshTokenRepository(db)

    def register(self, data: UserCreate) -> User:
        if self.user_repo.email_exists(str(data.email)):
            raise EmailAlreadyRegistered()
        if self.user_repo.username_exists(data.username):
            raise UsernameAlreadyRegistered()
        password_hash = security.hash_password(data.password)
        return self.user_repo.create(str(data.email), data.username, password_hash)

    def login(self, login: str, password: str) -> TokenPair:
        user = self.user_repo.get_by_username_or_email(login)
        if not user or not security.verify_password(password, user.password_hash):
            raise InvalidCredentials()
        return self._create_token_pair(user)

    def refresh(self, refresh_token: str) -> TokenPair:
        stored = self.refresh_token_repo.get_by_token(refresh_token)
        if stored is None:
            raise InvalidToken()
        if stored.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            self.refresh_token_repo.delete(stored)
            raise TokenExpired()
        user = self.user_repo.get_by_id(stored.user_id)
        if user is None:
            raise NotFound()
        self.refresh_token_repo.delete(stored)
        return self._create_token_pair(user)

    def logout(self, user_id: int) -> None:
        self.refresh_token_repo.delete_all_for_user(user_id)

    def _create_token_pair(self, user: User) -> TokenPair:
        access_token = security.create_access_token(user.id)
        refresh_token = security.generate_refresh_token()
        expires_at = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
        self.refresh_token_repo.create(user.id, refresh_token, expires_at)
        return TokenPair(access_token=access_token, refresh_token=refresh_token)
