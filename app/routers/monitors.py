from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Monitor, User
from app.schemas.monitor import MonitorCreate, MonitorRead, MonitorUpdate

router = APIRouter(prefix="/monitors", tags=["monitors"])


def get_owned_monitor(monitor_id: int, db: Session, user: User) -> Monitor:
    monitor = db.scalar(
        select(Monitor).where(Monitor.id == monitor_id, Monitor.user_id == user.id)
    )
    if monitor is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Monitor not found")
    return monitor


@router.post("", response_model=MonitorRead, status_code=status.HTTP_201_CREATED)
def create_monitor(
    data: MonitorCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    monitor = Monitor(
        user_id=user.id,
        name=data.name,
        url=str(data.url),
        interval_seconds=data.interval_seconds,
    )
    db.add(monitor)
    db.commit()
    db.refresh(monitor)
    return monitor


@router.get("", response_model=list[MonitorRead])
def list_monitors(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    query = (
        select(Monitor)
        .where(Monitor.user_id == user.id)
        .order_by(Monitor.id)
        .limit(limit)
        .offset(offset)
    )
    return db.scalars(query).all()


@router.get("/{monitor_id}", response_model=MonitorRead)
def get_monitor(
    monitor_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    return get_owned_monitor(monitor_id, db, user)


@router.patch("/{monitor_id}", response_model=MonitorRead)
def update_monitor(
    monitor_id: int,
    data: MonitorUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    monitor = get_owned_monitor(monitor_id, db, user)
    changes = data.model_dump(exclude_none=True)
    if "url" in changes:
        changes["url"] = str(changes["url"])
    for field, value in changes.items():
        setattr(monitor, field, value)
    db.commit()
    db.refresh(monitor)
    return monitor


@router.delete("/{monitor_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_monitor(
    monitor_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    monitor = get_owned_monitor(monitor_id, db, user)
    db.delete(monitor)
    db.commit()