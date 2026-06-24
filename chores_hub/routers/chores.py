from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from .. import crud, schemas
from ..database import get_db

router = APIRouter(prefix="/api/chores", tags=["chores"])


@router.get("", response_model=list[schemas.ChoreWithStatus])
def list_chores(
    active_only: bool = Query(default=True),
    db: Session = Depends(get_db),
):
    chores = crud.get_chores(db, active_only=active_only)
    return [crud._enrich_chore(c) for c in chores]


@router.post("", response_model=schemas.ChoreWithStatus, status_code=201)
def create_chore(chore: schemas.ChoreCreate, db: Session = Depends(get_db)):
    if chore.assigned_to_id is not None:
        if not crud.get_user(db, chore.assigned_to_id):
            raise HTTPException(status_code=404, detail="Assigned user not found")
    db_chore = crud.create_chore(db, chore)
    return crud._enrich_chore(db_chore)


@router.get("/{chore_id}", response_model=schemas.ChoreWithStatus)
def get_chore(chore_id: int, db: Session = Depends(get_db)):
    db_chore = crud.get_chore(db, chore_id)
    if not db_chore:
        raise HTTPException(status_code=404, detail="Chore not found")
    return crud._enrich_chore(db_chore)


@router.patch("/{chore_id}", response_model=schemas.ChoreWithStatus)
def update_chore(
    chore_id: int, chore: schemas.ChoreUpdate, db: Session = Depends(get_db)
):
    if chore.assigned_to_id is not None:
        if not crud.get_user(db, chore.assigned_to_id):
            raise HTTPException(status_code=404, detail="Assigned user not found")
    db_chore = crud.update_chore(db, chore_id, chore)
    if not db_chore:
        raise HTTPException(status_code=404, detail="Chore not found")
    return crud._enrich_chore(db_chore)


@router.delete("/{chore_id}", status_code=204)
def delete_chore(chore_id: int, db: Session = Depends(get_db)):
    if not crud.delete_chore(db, chore_id):
        raise HTTPException(status_code=404, detail="Chore not found")


@router.post("/{chore_id}/complete", response_model=schemas.ChoreCompletion, status_code=201)
def complete_chore(
    chore_id: int,
    completion: schemas.ChoreCompletionCreate,
    db: Session = Depends(get_db),
):
    if completion.completed_by_id is not None:
        if not crud.get_user(db, completion.completed_by_id):
            raise HTTPException(status_code=404, detail="User not found")
    result = crud.complete_chore(db, chore_id, completion)
    if result is None:
        raise HTTPException(status_code=404, detail="Chore not found")
    return result


@router.get("/{chore_id}/history", response_model=list[schemas.ChoreCompletion])
def get_chore_history(
    chore_id: int,
    limit: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    if not crud.get_chore(db, chore_id):
        raise HTTPException(status_code=404, detail="Chore not found")
    return crud.get_chore_history(db, chore_id, limit=limit)
