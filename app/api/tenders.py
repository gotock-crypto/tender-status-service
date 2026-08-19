from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.tender import TenderStatus
from app.schemas.tender import HistoryResponse, StatusUpdate, TenderCreate, TenderDetails, TenderResponse
from app.services.tender_service import (
    InvalidTransition,
    TenderNotFound,
    create_tender,
    delete_tender,
    get_tender,
    list_tenders,
    update_status,
    update_tender,
)

router = APIRouter(prefix="/tenders", tags=["tenders"])


@router.get("", response_model=list[TenderResponse])
def get_tenders(status_filter: TenderStatus | None = Query(default=None, alias="status"), db: Session = Depends(get_db)):
    return list_tenders(db, status_filter)


@router.post("", response_model=TenderResponse, status_code=status.HTTP_201_CREATED)
def post_tender(payload: TenderCreate, db: Session = Depends(get_db)):
    return create_tender(db, payload)


@router.get("/{tender_id}", response_model=TenderDetails)
def get_tender_details(tender_id: int, db: Session = Depends(get_db)):
    try:
        return get_tender(db, tender_id)
    except TenderNotFound as exc:
        raise HTTPException(404, "Tender not found") from exc


@router.put("/{tender_id}", response_model=TenderResponse)
def put_tender(tender_id: int, payload: TenderCreate, db: Session = Depends(get_db)):
    try:
        return update_tender(db, tender_id, payload)
    except TenderNotFound as exc:
        raise HTTPException(404, "Tender not found") from exc


@router.delete("/{tender_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_tender(tender_id: int, db: Session = Depends(get_db)):
    try:
        delete_tender(db, tender_id)
    except TenderNotFound as exc:
        raise HTTPException(404, "Tender not found") from exc


@router.patch("/{tender_id}/status", response_model=TenderDetails)
def patch_status(tender_id: int, payload: StatusUpdate, db: Session = Depends(get_db)):
    try:
        return update_status(db, tender_id, payload)
    except TenderNotFound as exc:
        raise HTTPException(404, "Tender not found") from exc
    except InvalidTransition as exc:
        raise HTTPException(409, str(exc)) from exc


@router.get("/{tender_id}/history", response_model=list[HistoryResponse])
def get_history(tender_id: int, db: Session = Depends(get_db)):
    try:
        return get_tender(db, tender_id).history
    except TenderNotFound as exc:
        raise HTTPException(404, "Tender not found") from exc
