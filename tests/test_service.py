from app.models.tender import TenderStatus
from app.services.tender_service import ALLOWED_TRANSITIONS


def test_status_machine_has_explicit_lifecycle():
    assert ALLOWED_TRANSITIONS[TenderStatus.DRAFT] == {TenderStatus.ACTIVE}
    assert ALLOWED_TRANSITIONS[TenderStatus.ACTIVE] == {TenderStatus.WON, TenderStatus.LOST}
    assert ALLOWED_TRANSITIONS[TenderStatus.WON] == set()
    assert ALLOWED_TRANSITIONS[TenderStatus.LOST] == set()


def test_terminal_statuses_have_no_outgoing_transitions():
    assert ALLOWED_TRANSITIONS[TenderStatus.WON] == set()
    assert ALLOWED_TRANSITIONS[TenderStatus.LOST] == set()
