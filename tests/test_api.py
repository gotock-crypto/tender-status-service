from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import pytest

from app.db.database import Base, get_db
from app.main import app

engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSession = sessionmaker(bind=engine)
Base.metadata.create_all(engine)


def override_db():
    db = TestingSession()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_db
client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_db():
    for table in reversed(Base.metadata.sorted_tables):
        with engine.begin() as conn:
            conn.execute(table.delete())


def create():
    response = client.post("/api/v1/tenders", json={
        "title": "Поставка серверов",
        "customer": "ООО Ромашка",
        "contract_number": "T-1",
        "initial_price": 12500000,
    })
    assert response.status_code == 201
    return response.json()["id"]


def test_create_starts_as_draft():
    data = client.post("/api/v1/tenders", json={"title": "Тест", "customer": "Заказчик", "initial_price": 1000}).json()
    assert data["status"] == "draft"


def test_crud():
    tender_id = create()
    response = client.put(f"/api/v1/tenders/{tender_id}", json={
        "title": "Обновлённый тендер", "customer": "Новый заказчик", "contract_number": "T-9", "initial_price": 99000
    })
    assert response.status_code == 200
    assert response.json()["title"] == "Обновлённый тендер"
    assert client.delete(f"/api/v1/tenders/{tender_id}").status_code == 204
    assert client.get(f"/api/v1/tenders/{tender_id}").status_code == 404


def test_status_change_creates_history():
    tender_id = create()
    response = client.patch(f"/api/v1/tenders/{tender_id}/status", json={"status":"won","changed_by":"ivan","reason":"Ручная корректировка"})
    assert response.status_code == 200
    history = client.get(f"/api/v1/tenders/{tender_id}/history").json()
    assert history[0]["old_status"] == "draft"
    assert history[0]["new_status"] == "won"
    assert history[0]["changed_by"] == "ivan"


def test_status_can_change_to_any_other_status():
    tender_id = create()
    for next_status in ["active", "lost", "active", "won"]:
        response = client.patch(f"/api/v1/tenders/{tender_id}/status", json={
            "status": next_status, "changed_by": "ivan", "reason": f"Переход в {next_status}"
        })
        assert response.status_code == 200
        assert response.json()["status"] == next_status


def test_same_status_is_rejected():
    tender_id = create()
    response = client.patch(f"/api/v1/tenders/{tender_id}/status", json={"status":"draft","changed_by":"ivan","reason":"same"})
    assert response.status_code == 409


def test_missing_tender():
    assert client.get("/api/v1/tenders/999").status_code == 404


def test_ui_and_assets():
    html = client.get("/")
    css = client.get("/static/style.css")
    js = client.get("/static/app.js")
    assert html.status_code == 200 and 'id="create-btn"' in html.text
    assert css.status_code == 200 and ".table-card" in css.text
    assert js.status_code == 200 and "/api/v1/tenders" in js.text
