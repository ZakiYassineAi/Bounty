from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

# --- Target Schemas ---

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

# --- Evidence Schemas ---
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

# --- Program Schemas ---

class RewardRead(BaseModel):
    id: int
    severity: str
    min_payout: Optional[int] = None
    max_payout: Optional[int] = None

    class Config:
        orm_mode = True

class PlatformRead(BaseModel):
    id: int
    name: str
    url: str

    class Config:
        orm_mode = True

class ProgramRead(BaseModel):
    id: int
    name: str
    program_url: str
    is_active: bool
    last_harvested_at: datetime
    scope: Dict[str, Any]
    platform: PlatformRead
    rewards: List[RewardRead]

    class Config:
        orm_mode = True

class ProgramReadBasic(BaseModel):
    """A simpler Program model for lists, without full scope/rewards."""
    id: int
    name: str
    program_url: str
    is_active: bool
    platform: PlatformRead

    class Config:
        orm_mode = True
