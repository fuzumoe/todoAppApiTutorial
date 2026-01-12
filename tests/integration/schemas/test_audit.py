import pytest

from app.schemas.audit import AuditPostRequest, AuditPostResponse, AuditRead
from app.schemas.common import ResponseEnvelope, Status

pytestmark = [pytest.mark.no_docker_cleanup]


def test_audit_post_request_alias_and_ignores_extra() -> None:
    payload = {
        "actorId": "u1",
        "action": "CREATE",
        "detail": "USER",
        "ignored": "field",
    }

    req = AuditPostRequest.model_validate(payload)

    assert req.actor_id == "u1"
    assert req.action == "CREATE"
    assert req.detail == "USER"

    dumped = req.model_dump()
    assert "ignored" not in dumped
    # Default dump uses snake_case
    assert dumped["actor_id"] == "u1"


def test_audit_read_serialization_aliases() -> None:
    audit = AuditRead(id="a1", actor_id="u7", action="UPDATE", detail="TASK")
    dumped = audit.model_dump(by_alias=True)
    assert dumped == {
        "id": "a1",
        "actorId": "u7",
        "action": "UPDATE",
        "detail": "TASK",
    }


def test_audit_post_response_envelope_defaults_and_data() -> None:
    audit = AuditRead(id="a2", actor_id="u2", action="DELETE", detail="PROJECT")
    resp = AuditPostResponse(message="Created", data=audit)

    assert isinstance(resp, ResponseEnvelope)
    assert resp.status == Status.success
    assert resp.message == "Created"
    assert resp.data == audit

    dumped = resp.model_dump(mode="json", by_alias=True)
    assert set(dumped.keys()) == {"status", "message", "data"}
    assert dumped["data"]["id"] == "a2"
    assert dumped["data"]["actorId"] == "u2"
