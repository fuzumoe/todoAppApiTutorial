import pytest
from pydantic import ValidationError

from app.models.enums import Role
from app.schemas.common import ResponseEnvelope, Status
from app.schemas.user import UserPostRequest, UserPostResponse, UserRead

pytestmark = [pytest.mark.no_docker_cleanup]


def test_user_post_request_valid_and_ignores_extra_fields() -> None:
    payload = {
        "username": "alice",
        "email": "alice@example.com",
        "password": "secret",
        "roles": [Role.USER, Role.ADMIN],
        "ignored": "field",  # should be ignored by model_config.extra="ignore"
    }

    req = UserPostRequest.model_validate(payload)

    # Required fields are set correctly
    assert req.username == "alice"
    assert req.email == "alice@example.com"
    assert req.password == "secret"
    assert req.roles == [Role.USER, Role.ADMIN]

    # Extra field should not be present in dump
    dumped = req.model_dump()
    assert "ignored" not in dumped


def test_user_post_request_email_validation() -> None:
    with pytest.raises(ValidationError):
        UserPostRequest(username="bob", email="not-an-email", password="x")


def test_user_post_request_roles_optional() -> None:
    req = UserPostRequest(username="carol", email="carol@example.com", password="x")
    assert req.roles is None


def test_user_read_serialization_aliases_and_enum_values() -> None:
    user = UserRead(
        id="u1",
        username="dave",
        email="dave@example.com",
        roles=[Role.USER, Role.MANAGER],
    )

    # Dump using aliases; enums should serialize to their values
    dumped = user.model_dump(by_alias=True, mode="json")
    assert dumped == {
        "id": "u1",
        "username": "dave",
        "email": "dave@example.com",
        "roles": ["USER", "MANAGER"],
    }


def test_user_post_response_envelope_defaults_and_data() -> None:
    user = UserRead(
        id="u2",
        username="eve",
        email="eve@example.com",
        roles=[Role.ADMIN],
    )

    resp = UserPostResponse(message="Created", data=user)

    # Envelope defaults
    assert isinstance(resp, ResponseEnvelope)
    assert resp.status == Status.success
    assert resp.message == "Created"
    assert resp.data == user

    # When serialized, nested model should respect aliases
    dumped = resp.model_dump(mode="json")
    # Envelope keys present
    assert set(dumped.keys()) == {"status", "message", "data"}
    # Nested data uses its own aliases when explicitly requested
    dumped_with_alias = resp.model_dump(mode="json")
    assert dumped_with_alias["data"]["id"] == "u2"
    assert dumped_with_alias["data"]["username"] == "eve"
    assert dumped_with_alias["data"]["roles"] == ["ADMIN"]
