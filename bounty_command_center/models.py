from typing import List, Optional
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship, JSON, Column


class Target(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    url: str
    # Use the `JSON` type from SQLModel/SQLAlchemy to store the list of strings
    scope: List[str] = Field(sa_column=Column(JSON))

    # The back_populates argument establishes a bidirectional relationship
    # between Target and Evidence
    evidence: List["Evidence"] = Relationship(back_populates="target")


class Evidence(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    finding_summary: str
    reproduction_steps: str = Field(default="")
    severity: str = Field(default="Informational")
    status: str = Field(default="new")

    # The foreign key links this model to the Target model
    target_id: Optional[int] = Field(default=None, foreign_key="target.id")

    # The relationship to the parent Target object
    target: Optional[Target] = Relationship(back_populates="evidence")


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, min_length=3, max_length=50)
    hashed_password: str
    role: str  # E.g., "admin", "researcher", "viewer"
