from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.core import security
from app.core.database import get_db
from app.core.exceptions import InvalidCredentials, InvalidToken, PermissionDenied
from app.models.user import User
from app.repositories.user_repository import UserRepository

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    user_id = security.decode_access_token(token)
    user = UserRepository(db).get_by_id(user_id)
    if user is None:
        raise InvalidToken()
    if not user.is_active:
        raise InvalidCredentials()
    return user


def get_current_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_admin:
        raise PermissionDenied()
    return user
