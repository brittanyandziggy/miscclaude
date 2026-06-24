from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


# --- User schemas ---

class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    color: str = Field(default="#4A90D9", pattern=r"^#[0-9A-Fa-f]{6}$")


class UserCreate(UserBase):
    pass


class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class User(UserBase):
    id: int
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Chore schemas ---

class ChoreBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    frequency_days: int = Field(default=7, ge=1, le=365)
    assigned_to_id: Optional[int] = None
    starts_at: Optional[datetime] = None


class ChoreCreate(ChoreBase):
    pass


class ChoreUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    frequency_days: Optional[int] = Field(None, ge=1, le=365)
    assigned_to_id: Optional[int] = None
    is_active: Optional[bool] = None
    starts_at: Optional[datetime] = None


class Chore(ChoreBase):
    id: int
    is_active: bool
    created_at: datetime
    assigned_to: Optional[User] = None

    model_config = {"from_attributes": True}


class ChoreWithStatus(Chore):
    last_completed_at: Optional[datetime]
    next_due_at: datetime
    is_overdue: bool
    days_until_due: int  # negative means overdue by that many days


# --- Completion schemas ---

class ChoreCompletionCreate(BaseModel):
    completed_by_id: Optional[int] = None
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None


class ChoreCompletion(BaseModel):
    id: int
    chore_id: int
    completed_by_id: Optional[int]
    completed_at: datetime
    notes: Optional[str]
    completed_by: Optional[User] = None

    model_config = {"from_attributes": True}


# --- Dashboard schema ---

class DashboardStats(BaseModel):
    overdue: list[ChoreWithStatus]
    due_today: list[ChoreWithStatus]
    due_this_week: list[ChoreWithStatus]
    upcoming: list[ChoreWithStatus]
    completed_recently: list[ChoreCompletion]
    total_chores: int
    total_overdue: int
