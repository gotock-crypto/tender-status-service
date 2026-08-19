from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.tender import TenderStatus


class TenderCreate(BaseModel):
    title: str = Field(min_length=1, max_length=500)
    customer: str = Field(min_length=1, max_length=300)
    contract_number: str | None = Field(default=None, max_length=100)
    initial_price: Decimal = Field(gt=0)


class StatusUpdate(BaseModel):
    status: TenderStatus
    changed_by: str = Field(min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=2000)


class TenderResponse(TenderCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: TenderStatus
    created_at: datetime
    updated_at: datetime


class HistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tender_id: int
    old_status: TenderStatus
    new_status: TenderStatus
    changed_by: str
    reason: str
    changed_at: datetime


class TenderDetails(TenderResponse):
    history: list[HistoryResponse]
