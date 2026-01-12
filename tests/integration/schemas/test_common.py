import pytest

from app.models.enums import TaskStatus
from app.schemas.common import Page, PageMeta, ResponseEnvelope, Status
from app.schemas.task import TaskRead

pytestmark = [pytest.mark.no_docker_cleanup]


def test_status_enum_values() -> None:
    assert Status.success.value == "success"
    assert Status.error.value == "error"


def test_response_envelope_defaults() -> None:
    resp = ResponseEnvelope[int]()
    assert resp.status == Status.success
    assert resp.message == "OK"
    assert resp.data is None


def test_response_envelope_with_data_and_json_dump() -> None:
    resp = ResponseEnvelope[str](message="All good", data="hello")
    dumped = resp.model_dump(mode="json")
    assert dumped == {"status": "success", "message": "All good", "data": "hello"}


def test_response_envelope_nested_model_uses_aliases_on_dump() -> None:
    task = TaskRead(
        id="t1",
        description="Spec review",
        project_id="p1",
        assigned_to=None,
        status=TaskStatus.PENDING,
    )
    resp = ResponseEnvelope[TaskRead](message="Wrapped", data=task)
    dumped = resp.model_dump(mode="json", by_alias=True)
    assert set(dumped.keys()) == {"status", "message", "data"}
    assert dumped["data"]["id"] == "t1"
    assert dumped["data"]["projectId"] == "p1"
    assert dumped["data"]["assignedTo"] is None
    assert dumped["data"]["status"] == "PENDING"


def test_page_meta_and_page_with_primitives() -> None:
    meta = PageMeta(total=42, limit=10, offset=20)
    page = Page[int](items=[1, 2, 3], meta=meta)
    dumped = page.model_dump()
    assert dumped == {
        "items": [1, 2, 3],
        "meta": {"total": 42, "limit": 10, "offset": 20},
    }


def test_page_with_models_and_alias_dump() -> None:
    items = [
        TaskRead(
            id="t1",
            description="A",
            project_id="p",
            assigned_to=None,
            status=TaskStatus.ASSIGNED,
        ),
        TaskRead(
            id="t2",
            description="B",
            project_id="p",
            assigned_to="u1",
            status=TaskStatus.COMPLETED,
        ),
    ]
    meta = PageMeta(total=2, limit=10, offset=0)
    page = Page[TaskRead](items=items, meta=meta)
    dumped = page.model_dump(by_alias=True, mode="json")
    assert dumped["meta"] == {"total": 2, "limit": 10, "offset": 0}
    assert dumped["items"][0]["projectId"] == "p"
    assert dumped["items"][1]["assignedTo"] == "u1"
    assert dumped["items"][1]["status"] == "COMPLETED"
