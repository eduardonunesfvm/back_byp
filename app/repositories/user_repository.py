from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.user import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_username_or_email(self, login: str) -> User | None:
        stmt = select(User).where(
            or_(User.username == login, User.email == login)
        )
        return self.db.scalars(stmt).first()

    def email_exists(self, email: str) -> bool:
        stmt = select(User.id).where(User.email == email).limit(1)
        return self.db.scalars(stmt).first() is not None

    def username_exists(self, username: str) -> bool:
        stmt = select(User.id).where(User.username == username).limit(1)
        return self.db.scalars(stmt).first() is not None

    def create(self, email: str, username: str, password_hash: str) -> User:
        user = User(email=email, username=username, password_hash=password_hash)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
