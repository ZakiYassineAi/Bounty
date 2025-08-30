from typing import Optional
from sqlmodel import Session, select
from .models import User
from .security import get_password_hash

class UserManager:
    """Manages user-related database operations."""

    def get_user_by_username(self, db: Session, username: str) -> Optional[User]:
        """Retrieves a user from the database by their username."""
        statement = select(User).where(User.username == username)
        return db.exec(statement).first()

    def create_user(self, db: Session, username: str, password: str, role: str) -> Optional[User]:
        """Creates a new user and saves them to the database."""
        if self.get_user_by_username(db, username):
            return None  # User already exists

        hashed_password = get_password_hash(password)
        new_user = User(username=username, hashed_password=hashed_password, role=role)

        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
