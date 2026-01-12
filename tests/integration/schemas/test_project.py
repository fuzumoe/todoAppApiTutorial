import pytest

from app.schemas.common import ResponseEnvelope, Status
from app.schemas.project import ProjectPostRequest, ProjectPostResponse, ProjectRead

pytestmark = [pytest.mark.no_docker_cleanup]


def test_project_post_request_aliases_and_ignores_extra() -> None:
    payload = {
        "name": "Alpha",
        "description": "First project",
        "ownerId": "u123",
        "ignored": "field",
    }

    req = ProjectPostRequest.model_validate(payload)

    assert req.name == "Alpha"
    assert req.description == "First project"
    assert req.owner_id == "u123"

    dumped = req.model_dump()
    assert "ignored" not in dumped
    # Default dump uses snake_case
    assert dumped["owner_id"] == "u123"


def test_project_post_request_optional_description() -> None:
    req = ProjectPostRequest.model_validate({"name": "Beta", "ownerId": "u999"})
    assert req.description is None


def test_project_read_serialization_aliases() -> None:
    project = ProjectRead(id="p1", name="Gamma", description=None, owner_id="u777")
    dumped = project.model_dump(by_alias=True)
    assert dumped == {
        "id": "p1",
        "name": "Gamma",
        "description": None,
        "ownerId": "u777",
    }


def test_project_post_response_envelope_defaults_and_data() -> None:
    project = ProjectRead(id="p2", name="Delta", description="", owner_id="u42")

    resp = ProjectPostResponse(message="Created", data=project)

    assert isinstance(resp, ResponseEnvelope)
    assert resp.status == Status.success
    assert resp.message == "Created"
    assert resp.data == project

    dumped = resp.model_dump(mode="json", by_alias=True)
    assert set(dumped.keys()) == {"status", "message", "data"}
    assert dumped["data"]["id"] == "p2"
    assert dumped["data"]["ownerId"] == "u42"
