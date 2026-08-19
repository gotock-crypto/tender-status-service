from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.tender import Tender, TenderStatus, TenderStatusHistory
from app.schemas.tender import StatusUpdate, TenderCreate


# A tender follows a small, explicit lifecycle. Terminal statuses cannot be
# reopened, which prevents contradictory audit histories such as WON -> ACTIVE.
ALLOWED_TRANSITIONS = {
    TenderStatus.DRAFT: {TenderStatus.ACTIVE},
    TenderStatus.ACTIVE: {TenderStatus.WON, TenderStatus.LOST},
    TenderStatus.WON: set(),
    TenderStatus.LOST: set(),
}


class TenderNotFound(Exception):
    pass


class InvalidTransition(Exception):
    pass


def create_tender(db: Session, payload: TenderCreate) -> Tender:
    tender = Tender(**payload.model_dump(), status=TenderStatus.DRAFT)
    db.add(tender)
    db.commit()
    db.refresh(tender)
    return tender


def list_tenders(db: Session, status: TenderStatus | None = None) -> list[Tender]:
    stmt = select(Tender).order_by(Tender.created_at.desc())
    if status:
        stmt = stmt.where(Tender.status == status)
    return list(db.scalars(stmt).all())


def get_tender(db: Session, tender_id: int) -> Tender:
    tender = db.get(Tender, tender_id)
    if tender is None:
        raise TenderNotFound
    return tender


def update_tender(db: Session, tender_id: int, payload: TenderCreate) -> Tender:
    tender = get_tender(db, tender_id)
    for key, value in payload.model_dump().items():
        setattr(tender, key, value)
    tender.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(tender)
    return tender


def delete_tender(db: Session, tender_id: int) -> None:
    tender = get_tender(db, tender_id)
    db.delete(tender)
    db.commit()


def update_status(db: Session, tender_id: int, payload: StatusUpdate) -> Tender:
    tender = get_tender(db, tender_id)
    old_status = tender.status

    if payload.status == old_status:
        raise InvalidTransition("Tender already has this status")
    if payload.status not in ALLOWED_TRANSITIONS[old_status]:
        raise InvalidTransition(
            f"Transition {old_status.value} -> {payload.status.value} is not allowed"
        )

    now = datetime.now(timezone.utc)
    tender.status = payload.status
    tender.updated_at = now
    db.add(TenderStatusHistory(
        tender_id=tender.id,
        old_status=old_status,
        new_status=payload.status,
        changed_by=payload.changed_by,
        reason=payload.reason,
        changed_at=now,
    ))
    db.commit()
    db.refresh(tender)
    return tender
