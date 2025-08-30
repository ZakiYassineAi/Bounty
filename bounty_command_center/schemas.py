from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- Target Schemas (V1 - to be deprecated) ---

class TargetBase(BaseModel):
    name: str
    url: str
    scope: List[str]

class TargetCreate(TargetBase):
    pass

class TargetRead(TargetBase):
    id: int

class TargetUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    scope: Optional[List[str]] = None

# --- Evidence Schemas (V1 - to be deprecated) ---
class EvidenceBase(BaseModel):
    finding_summary: str
    reproduction_steps: str
    severity: str
    status: str = "new"
    target_id: int

class EvidenceCreate(EvidenceBase):
    pass

class EvidenceRead(EvidenceBase):
    id: int
    timestamp: str

class EvidenceUpdate(BaseModel):
    finding_summary: Optional[str] = None
    reproduction_steps: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None

# --- User Schemas ---
class UserBase(BaseModel):
    username: str
    role: str

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int

# --- Program Schemas (V2) ---

class PlatformRead(BaseModel):
    id: int
    name: str
    url: str

    class Config:
        orm_mode = True

class ProgramReadBasic(BaseModel):
    """A lighter Program model for list views."""
    id: int
    name: str
    program_url: str
    status: str
    offers_bounties: bool
    min_payout: Optional[int] = None
    max_payout: Optional[int] = None
    platform: PlatformRead
    last_seen_at: datetime

    class Config:
        orm_mode = True

class PaginatedProgramResponse(BaseModel):
    """Response model for paginated program lists."""
    items: List[ProgramReadBasic]
    next_cursor: Optional[int] = None

class ProgramRead(ProgramReadBasic):
    """Full Program model for detail view."""
    # This will eventually be expanded with assets, versions, etc.
    assets: List[Dict[str, Any]] = [] # Placeholder for now
    versions: List[Dict[str, Any]] = [] # Placeholder for now

    class Config:
        orm_mode = True
