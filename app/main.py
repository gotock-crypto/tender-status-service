from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.tenders import router as tenders_router
from app.db.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TenderFlow",
    description="Tender status tracking service with CRUD and audit history.",
    version="1.0.0",
)

app.include_router(tenders_router, prefix="/api/v1")

static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
def index() -> FileResponse:
    return FileResponse(static_dir / "index.html")
