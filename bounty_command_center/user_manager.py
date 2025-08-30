from typing import Optional
from sqlmodel import Session, select
from .database import engine
from .models import User
from .auth import get_password_hash

class UserManager:
    """Manages user-related database operations."""

    def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Retrieves a user from the database by their username.

        Args:
            username: The username to search for.

        Returns:
            The User object if found, otherwise None.
        """
        with Session(engine) as session:
            statement = select(User).where(User.username == username)
            return session.exec(statement).first()

    def create_user(self, username: str, password: str, role: str) -> Optional[User]:
        """
        Creates a new user and saves them to the database.

        Args:
            username: The desired username.
            password: The plain-text password.
            role: The user's role (e.g., 'admin', 'researcher').

        Returns:
            The created User object if successful, otherwise None (e.g., if username exists).
        """
        if self.get_user_by_username(username):
            return None  # User already exists

        hashed_password = get_password_hash(password)
        new_user = User(username=username, hashed_password=hashed_password, role=role)

        with Session(engine) as session:
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            return new_user
