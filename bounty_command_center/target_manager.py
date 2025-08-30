from typing import List, Optional, Dict, Any
from sqlmodel import Session, select
from .models import Target

class TargetManager:
    """Manages CRUD operations for targets in the database."""

    def add_target(self, db: Session, name: str, url: str, scope: List[str]) -> Optional[Target]:
        """Adds a new target to the database if the name is unique."""
        if self.get_target_by_name(db, name):
            return None

        new_target = Target(name=name, url=url, scope=scope)
        db.add(new_target)
        db.commit()
        db.refresh(new_target)
        return new_target

    def get_target_by_name(self, db: Session, name: str) -> Optional[Target]:
        """Retrieves a single target by its name."""
        statement = select(Target).where(Target.name == name)
        return db.exec(statement).first()

    def get_target_by_id(self, db: Session, target_id: int) -> Optional[Target]:
        """Retrieves a single target by its ID."""
        return db.get(Target, target_id)

    def get_all_targets(self, db: Session, skip: int = 0, limit: int = 100) -> List[Target]:
        """Retrieves a list of all targets with pagination."""
        statement = select(Target).offset(skip).limit(limit)
        return db.exec(statement).all()

    def remove_target(self, db: Session, name: str) -> bool:
        """Removes a target by its name."""
        target = self.get_target_by_name(db, name)
        if target:
            db.delete(target)
            db.commit()
            return True
        return False

    def remove_target_by_id(self, db: Session, target_id: int) -> bool:
        """Removes a target by its ID."""
        target = db.get(Target, target_id)
        if target:
            db.delete(target)
            db.commit()
            return True
        return False

    def update_target(self, db: Session, target_id: int, update_data: Dict[str, Any]) -> Optional[Target]:
        """Updates a target's attributes."""
        target = db.get(Target, target_id)
        if not target:
            return None

        for key, value in update_data.items():
            setattr(target, key, value)

        db.add(target)
        db.commit()
        db.refresh(target)
        return target
