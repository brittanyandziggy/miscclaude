from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    color = Column(String(7), default="#4A90D9")  # hex color for display
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    chores = relationship("Chore", back_populates="assigned_to", foreign_keys="Chore.assigned_to_id")
    completions = relationship("ChoreCompletion", back_populates="completed_by")


class Chore(Base):
    __tablename__ = "chores"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    # How many days between completions (1=daily, 7=weekly, 14=biweekly, 30=monthly, etc.)
    frequency_days = Column(Integer, nullable=False, default=7)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    # Anchor date: when the chore cycle started (used to calculate due date before first completion)
    starts_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    assigned_to = relationship("User", back_populates="chores", foreign_keys=[assigned_to_id])
    completions = relationship(
        "ChoreCompletion",
        back_populates="chore",
        order_by="ChoreCompletion.completed_at.desc()",
        cascade="all, delete-orphan",
    )


class ChoreCompletion(Base):
    __tablename__ = "chore_completions"

    id = Column(Integer, primary_key=True, index=True)
    chore_id = Column(Integer, ForeignKey("chores.id"), nullable=False)
    completed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    completed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    notes = Column(Text, nullable=True)

    chore = relationship("Chore", back_populates="completions")
    completed_by = relationship("User", back_populates="completions")
