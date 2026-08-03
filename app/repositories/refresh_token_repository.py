from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_token(self, token: str) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token == token)
        return self.db.scalars(stmt).first()

    def create(self, user_id: int, token: str, expires_at: datetime) -> RefreshToken:
        rt = RefreshToken(user_id=user_id, token=token, expires_at=expires_at)
        self.db.add(rt)
        self.db.commit()
        return rt

    def delete(self, rt: RefreshToken) -> None:
        self.db.delete(rt)
        self.db.commit()

    def delete_all_for_user(self, user_id: int) -> None:
        stmt = select(RefreshToken).where(RefreshToken.user_id == user_id)
        for rt in self.db.scalars(stmt):
            self.db.delete(rt)
        self.db.commit()
