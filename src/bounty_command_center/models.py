from typing import List, Optional
from datetime import datetime, timezone
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
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
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
    role: str # E.g., "admin", "researcher", "viewer"

class ProgramRaw(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    platform: str = Field(index=True)
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    data: str  # Storing as a string, could be JSON or HTML
    etag: Optional[str] = Field(default=None)
    last_modified: Optional[str] = Field(default=None)

class ProgramClean(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    url: str = Field(unique=True)
    platform: str = Field(index=True)
    scope: List[str] = Field(sa_column=Column(JSON))
    vulnerability_types: List[str] = Field(default=[], sa_column=Column(JSON))
    min_bounty: Optional[float] = Field(default=None)
    max_bounty: Optional[float] = Field(default=None)
    status: str = Field(default="public", index=True)
    last_updated: Optional[datetime] = Field(default=None)
    acceptance_rate: Optional[float] = Field(default=None)

class ProgramInvalid(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    platform: str = Field(index=True)
    raw_data: str
    error_message: str
    fetched_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
