from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.api.tenders import router as tenders_router
from app.db.database import Base, SessionLocal, engine
from app.models.tender import Tender, TenderStatus, TenderStatusHistory

STATIC_DIR = Path(__file__).resolve().parent / "static"


def seed_demo_data() -> None:
    db: Session = SessionLocal()
    try:
        if db.query(Tender).count() > 0:
            return
        now = datetime.now(timezone.utc)
        demo = [
            ("Техническое обслуживание газового оборудования", "Администрация муниципального района", "44-01/2026", Decimal("12500000.00"), TenderStatus.ACTIVE),
            ("Ремонт автомобильных дорог", "ГКУ «Дороги региона»", "44-17/2026", Decimal("38750000.00"), TenderStatus.DRAFT),
            ("Поставка компьютерного оборудования", "ГБУ «Центр цифрового развития»", "44-23/2026", Decimal("8450000.00"), TenderStatus.WON),
            ("Капитальный ремонт школы №18", "Департамент образования", "44-31/2026", Decimal("56200000.00"), TenderStatus.LOST),
            ("Поставка спецодежды для сотрудников", "Городская клиническая больница", "44-42/2026", Decimal("2190000.00"), TenderStatus.ACTIVE),
            ("Обслуживание систем вентиляции", "ГБУ «Городской сервис»", "44-51/2026", Decimal("3780000.00"), TenderStatus.DRAFT),
        ]
        for i, (title, customer, number, price, status) in enumerate(demo):
            created = now - timedelta(days=20 - i * 2)
            tender = Tender(title=title, customer=customer, contract_number=number, initial_price=price, status=status, created_at=created, updated_at=created)
            db.add(tender)
            db.flush()
            if status in (TenderStatus.WON, TenderStatus.LOST):
                history_time = created + timedelta(days=5)
                db.add(TenderStatusHistory(
                    tender_id=tender.id,
                    old_status=TenderStatus.ACTIVE,
                    new_status=status,
                    changed_by="Анна Петрова",
                    reason="Результат закупочной процедуры",
                    changed_at=history_time,
                ))
                tender.updated_at = history_time
        db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_demo_data()
    yield


app = FastAPI(title="TenderFlow", description="Tender status tracking microservice with audit history.", version="2.0.0", lifespan=lifespan)
app.include_router(tenders_router, prefix="/api/v1")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")
