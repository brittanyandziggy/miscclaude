from datetime import datetime, timedelta, timezone
from typing import Optional

from sqlalchemy.orm import Session

from . import models, schemas


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _make_aware(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _chore_next_due(chore: models.Chore) -> datetime:
    last = chore.completions[0].completed_at if chore.completions else None
    anchor = _make_aware(last) if last else _make_aware(chore.starts_at)
    return anchor + timedelta(days=chore.frequency_days)


def _enrich_chore(chore: models.Chore) -> schemas.ChoreWithStatus:
    now = _now()
    last_completed_at = (
        _make_aware(chore.completions[0].completed_at) if chore.completions else None
    )
    next_due_at = _chore_next_due(chore)
    delta = next_due_at - now
    days_until_due = int(delta.total_seconds() // 86400)

    return schemas.ChoreWithStatus(
        **schemas.Chore.model_validate(chore).model_dump(),
        last_completed_at=last_completed_at,
        next_due_at=next_due_at,
        is_overdue=next_due_at < now,
        days_until_due=days_until_due,
    )


# --- Users ---

def get_users(db: Session) -> list[models.User]:
    return db.query(models.User).all()


def get_user(db: Session, user_id: int) -> Optional[models.User]:
    return db.query(models.User).filter(models.User.id == user_id).first()


def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    db_user = models.User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, user_id: int, user: schemas.UserUpdate) -> Optional[models.User]:
    db_user = get_user(db, user_id)
    if not db_user:
        return None
    for field, value in user.model_dump(exclude_none=True).items():
        setattr(db_user, field, value)
    db.commit()
    db.refresh(db_user)
    return db_user


def delete_user(db: Session, user_id: int) -> bool:
    db_user = get_user(db, user_id)
    if not db_user:
        return False
    db.delete(db_user)
    db.commit()
    return True


# --- Chores ---

def get_chores(db: Session, active_only: bool = True) -> list[models.Chore]:
    q = db.query(models.Chore)
    if active_only:
        q = q.filter(models.Chore.is_active == True)
    return q.all()


def get_chore(db: Session, chore_id: int) -> Optional[models.Chore]:
    return db.query(models.Chore).filter(models.Chore.id == chore_id).first()


def create_chore(db: Session, chore: schemas.ChoreCreate) -> models.Chore:
    data = chore.model_dump()
    if data.get("starts_at") is None:
        data["starts_at"] = _now()
    db_chore = models.Chore(**data)
    db.add(db_chore)
    db.commit()
    db.refresh(db_chore)
    return db_chore


def update_chore(db: Session, chore_id: int, chore: schemas.ChoreUpdate) -> Optional[models.Chore]:
    db_chore = get_chore(db, chore_id)
    if not db_chore:
        return None
    for field, value in chore.model_dump(exclude_none=True).items():
        setattr(db_chore, field, value)
    db.commit()
    db.refresh(db_chore)
    return db_chore


def delete_chore(db: Session, chore_id: int) -> bool:
    db_chore = get_chore(db, chore_id)
    if not db_chore:
        return False
    db.delete(db_chore)
    db.commit()
    return True


# --- Completions ---

def complete_chore(
    db: Session, chore_id: int, completion: schemas.ChoreCompletionCreate
) -> Optional[models.ChoreCompletion]:
    db_chore = get_chore(db, chore_id)
    if not db_chore:
        return None
    data = completion.model_dump()
    if data.get("completed_at") is None:
        data["completed_at"] = _now()
    db_completion = models.ChoreCompletion(chore_id=chore_id, **data)
    db.add(db_completion)
    db.commit()
    db.refresh(db_completion)
    # Reload chore so completions relationship is refreshed
    db.refresh(db_chore)
    return db_completion


def get_chore_history(
    db: Session, chore_id: int, limit: int = 50
) -> list[models.ChoreCompletion]:
    return (
        db.query(models.ChoreCompletion)
        .filter(models.ChoreCompletion.chore_id == chore_id)
        .order_by(models.ChoreCompletion.completed_at.desc())
        .limit(limit)
        .all()
    )


def get_recent_completions(db: Session, limit: int = 20) -> list[models.ChoreCompletion]:
    return (
        db.query(models.ChoreCompletion)
        .order_by(models.ChoreCompletion.completed_at.desc())
        .limit(limit)
        .all()
    )


# --- Dashboard ---

def get_dashboard(db: Session) -> schemas.DashboardStats:
    now = _now()
    end_of_today = now.replace(hour=23, minute=59, second=59)
    end_of_week = now + timedelta(days=7)

    chores = get_chores(db, active_only=True)
    enriched = [_enrich_chore(c) for c in chores]

    overdue = [c for c in enriched if c.is_overdue]
    due_today = [c for c in enriched if not c.is_overdue and c.next_due_at <= end_of_today]
    due_this_week = [
        c for c in enriched
        if not c.is_overdue and end_of_today < c.next_due_at <= end_of_week
    ]
    upcoming = [c for c in enriched if c.next_due_at > end_of_week]

    overdue.sort(key=lambda c: c.next_due_at)
    due_today.sort(key=lambda c: c.next_due_at)
    due_this_week.sort(key=lambda c: c.next_due_at)
    upcoming.sort(key=lambda c: c.next_due_at)

    return schemas.DashboardStats(
        overdue=overdue,
        due_today=due_today,
        due_this_week=due_this_week,
        upcoming=upcoming,
        completed_recently=get_recent_completions(db),
        total_chores=len(chores),
        total_overdue=len(overdue),
    )
