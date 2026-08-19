def test_status_machine_allows_manual_changes():
    from app.services.tender_service import ALLOWED_TRANSITIONS
    from app.models.tender import TenderStatus

    for status in TenderStatus:
        assert status not in ALLOWED_TRANSITIONS[status]
        assert set(ALLOWED_TRANSITIONS[status]) == set(TenderStatus) - {status}
