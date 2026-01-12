import pytest

from app.models.enums import TaskStatus
from app.schemas.common import ResponseEnvelope, Status
from app.schemas.task import TaskPostRequest, TaskPostResponse, TaskRead

pytestmark = [pytest.mark.no_docker_cleanup]


def test_task_post_request_valid_aliases_and_ignores_extra_fields() -> None:
    payload = {
        "description": "Write docs",
        "projectId": "p1",
        "assignedTo": "u1",
        "status": TaskStatus.ASSIGNED,
        "ignored": "field",  # should be ignored
    }

    req = TaskPostRequest.model_validate(payload)

    # Internal fields populated via aliases
    assert req.description == "Write docs"
    assert req.project_id == "p1"
    assert req.assigned_to == "u1"
    assert req.status == TaskStatus.ASSIGNED

    dumped = req.model_dump()
    assert "ignored" not in dumped
    # Default dump uses snake_case field names
    assert dumped["project_id"] == "p1"
    assert dumped["assigned_to"] == "u1"


def test_task_post_request_optional_fields() -> None:
    # assignedTo and status are optional
    req = TaskPostRequest.model_validate(
        {
            "description": "Set up CI",
            "projectId": "p2",
        }
    )
    assert req.assigned_to is None
    assert req.status is None


def test_task_read_serialization_aliases_and_enum_values() -> None:
    task = TaskRead(
        id="t1",
        description="Implement feature",
        project_id="pX",
        assigned_to=None,
        status=TaskStatus.PENDING,
    )

    dumped = task.model_dump(by_alias=True, mode="json")
    assert dumped == {
        "id": "t1",
        "description": "Implement feature",
        "projectId": "pX",
        "assignedTo": None,
        "status": "PENDING",
    }


def test_task_post_response_envelope_defaults_and_data() -> None:
    task = TaskRead(
        id="t2",
        description="QA pass",
        project_id="pY",
        assigned_to="u9",
        status=TaskStatus.COMPLETED,
    )

    resp = TaskPostResponse(message="Created", data=task)

    assert isinstance(resp, ResponseEnvelope)
    assert resp.status == Status.success
    assert resp.message == "Created"
    assert resp.data == task

    dumped = resp.model_dump(mode="json", by_alias=True)
    assert set(dumped.keys()) == {"status", "message", "data"}
    assert dumped["data"]["id"] == "t2"
    assert dumped["data"]["projectId"] == "pY"
    assert dumped["data"]["assignedTo"] == "u9"
    assert dumped["data"]["status"] == "COMPLETED"
