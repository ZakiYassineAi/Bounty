from sqlmodel import Session, select
from .database import engine
from .models import Target

class TargetManager:
    """Manages the lifecycle of bug bounty targets using a database."""

    def add_target(self, name: str, url: str, scope: list[str]) -> bool:
        """
        Adds a new target to the database.
        Returns True on success, False on failure (e.g., duplicate).
        """
        with Session(engine) as session:
            # Check if a target with the same name already exists
            existing = session.exec(select(Target).where(Target.name == name)).first()
            if existing:
                print(f"Error: A target with the name '{name}' already exists.")
                return False

            new_target = Target(name=name, url=url, scope=scope)
            session.add(new_target)
            session.commit()
            print(f"Successfully added target: {name}")
            return True

    def remove_target(self, name: str) -> bool:
        """
        Removes a target by name from the database.
        Returns True on success, False if not found.
        """
        with Session(engine) as session:
            target_to_delete = session.exec(select(Target).where(Target.name == name)).first()

            if target_to_delete:
                session.delete(target_to_delete)
                session.commit()
                print(f"Successfully removed target: {name}")
                return True
            else:
                print(f"Error: No target found with the name '{name}'.")
                return False

    def list_targets(self):
        """Displays all current targets from the database."""
        with Session(engine) as session:
            targets = session.exec(select(Target)).all()

            print("\n--- Current Targets ---")
            if not targets:
                print("No targets in the database.")
                return

            for i, target in enumerate(targets):
                print(f"{i+1}. Name: {target.name}")
                print(f"   URL: {target.url}")
                print(f"   Scope: {', '.join(target.scope)}")
                print("-" * 20)

    def get_target_by_name(self, name: str) -> Target | None:
        """Finds and returns a target by name from the database."""
        with Session(engine) as session:
            target = session.exec(select(Target).where(Target.name == name)).first()
            return target

    def get_all_targets(self) -> list[Target]:
        """Returns a list of all target objects."""
        with Session(engine) as session:
            return session.exec(select(Target)).all()
