from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel, Relationship, JSON, Column, UniqueConstraint

# --- V2 Models for Bounty Program Harvesting ---

class Platform(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True) # e.g., "HackerOne"
    url: str # e.g., "https://hackerone.com"

    programs: List["Program"] = Relationship(back_populates="platform")

class Program(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("platform_id", "external_id", name="uq_program_platform_external_id"),)

    id: Optional[int] = Field(default=None, primary_key=True)
    external_id: str = Field(index=True) # The ID from the platform, e.g., "1337" or "gitlab"
    name: str = Field(index=True)
    program_url: str = Field(unique=True)

    status: str # e.g., "active", "paused", "private"
    offers_bounties: bool = Field(default=False)

    min_payout: Optional[int] = None
    max_payout: Optional[int] = None
    currency: Optional[str] = None # e.g., "USD"

    # These fields can be enriched over time
    roi_score: Optional[float] = None
    competition_index: Optional[float] = None

    first_seen_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    platform_id: int = Field(foreign_key="platform.id")
    platform: "Platform" = Relationship(back_populates="programs")

    assets: List["Asset"] = Relationship(back_populates="program")
    versions: List["ProgramVersion"] = Relationship(back_populates="program")

class Asset(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    asset_type: str # e.g., "URL", "CIDR", "MOBILE_APP"
    identifier: str
    in_scope: bool = True

    program_id: int = Field(foreign_key="program.id")
    program: "Program" = Relationship(back_populates="assets")

class ProgramVersion(SQLModel, table=True):
    """Stores a snapshot of a program's key details whenever they change."""
    id: Optional[int] = Field(default=None, primary_key=True)
    snapshot: Dict[str, Any] = Field(sa_column=Column(JSON))
    version_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    program_id: int = Field(foreign_key="program.id")
    program: "Program" = Relationship(back_populates="versions")

class PlatformMetadata(SQLModel, table=True):
    """Stores metadata about harvester runs for each platform, e.g., ETags."""
    id: Optional[int] = Field(default=None, primary_key=True)
    platform_name: str = Field(unique=True, index=True)
    last_run_metadata: Dict[str, Any] = Field(sa_column=Column(JSON), default={})

# --- Existing Models (to be deprecated) ---

class Target(SQLModel, table=True):
    __tablename__ = "target_v1" # Rename table to avoid conflict
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    url: str
    scope: List[str] = Field(sa_column=Column(JSON))
    evidence: List["Evidence"] = Relationship(back_populates="target")

class Evidence(SQLModel, table=True):
    __tablename__ = "evidence_v1" # Rename table to avoid conflict
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finding_summary: str
    reproduction_steps: str = Field(default="")
    severity: str = Field(default="Informational")
    status: str = Field(default="new")
    target_id: Optional[int] = Field(default=None, foreign_key="target_v1.id")
    target: Optional[Target] = Relationship(back_populates="evidence")

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, min_length=3, max_length=50)
    hashed_password: str
    role: str
