from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from .database import engine
from .models import Target

class TargetManager:
    """Manages CRUD operations for targets in the database."""

    def add_target(self, name: str, url: str, scope: List[str]) -> Optional[Target]:
        """
        Adds a new target to the database if the name is unique.

        Args:
            name: The unique name for the target.
            url: The primary URL of the target.
            scope: A list of strings defining the target's scope.

        Returns:
            The created Target object if successful, otherwise None.
        """
        # First, check if a target with the same name already exists
        if self.get_target_by_name(name):
            return None

        new_target = Target(name=name, url=url, scope=scope)
        with Session(engine) as session:
            session.add(new_target)
            session.commit()
            session.refresh(new_target)
            return new_target

    def get_target_by_name(self, name: str) -> Optional[Target]:
        """Retrieves a single target by its name."""
        with Session(engine) as session:
            statement = select(Target).where(Target.name == name)
            return session.exec(statement).first()

    def get_target_by_id(self, target_id: int) -> Optional[Target]:
        """Retrieves a single target by its ID."""
        with Session(engine) as session:
            return session.get(Target, target_id)

    def get_all_targets(self, skip: int = 0, limit: int = 100) -> List[Target]:
        """Retrieves a list of all targets with pagination."""
        with Session(engine) as session:
            statement = select(Target).offset(skip).limit(limit)
            return session.exec(statement).all()

    def remove_target(self, name: str) -> bool:
        """Removes a target by its name."""
        with Session(engine) as session:
            target = self.get_target_by_name(name)
            if target:
                session.delete(target)
                session.commit()
                return True
            return False

    def remove_target_by_id(self, target_id: int) -> bool:
        """Removes a target by its ID."""
        with Session(engine) as session:
            target = session.get(Target, target_id)
            if target:
                session.delete(target)
                session.commit()
                return True
            return False

    def update_target(self, target_id: int, update_data: Dict[str, Any]) -> Optional[Target]:
        """
        Updates a target's attributes.

        Args:
            target_id: The ID of the target to update.
            update_data: A dictionary with the fields to update.

        Returns:
            The updated Target object, or None if not found.
        """
        with Session(engine) as session:
            target = session.get(Target, target_id)
            if not target:
                return None

            for key, value in update_data.items():
                setattr(target, key, value)

            session.add(target)
            session.commit()
            session.refresh(target)
            return target
