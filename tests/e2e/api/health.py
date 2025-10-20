import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.main import app

pytestmark = [pytest.mark.no_docker_cleanup]


@pytest.fixture(scope="module")
def client() -> TestClient:
    """Create a test client for the FastAPI app."""
    return TestClient(app)


def test_health_endpoint_returns_200(client: TestClient) -> None:
    """Test that the health endpoint returns 200 OK."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK


def test_health_endpoint_returns_json(client: TestClient) -> None:
    """Test that the health endpoint returns JSON response."""
    response = client.get("/health")
    assert response.headers["content-type"] == "application/json"


def test_health_endpoint_response_structure(client: TestClient) -> None:
    """Test that the health endpoint returns the expected structure."""
    response = client.get("/health")
    data = response.json()

    assert "status" in data
    assert "config_source" in data
    assert "app_name" in data
    assert "version" in data


def test_health_endpoint_status_value(client: TestClient) -> None:
    """Test that the health endpoint returns 'healthy' status."""
    response = client.get("/health")
    data = response.json()

    assert data["status"] == "healthy"


def test_health_endpoint_config_source(client: TestClient) -> None:
    """Test that the health endpoint returns config_source."""
    response = client.get("/health")
    data = response.json()

    assert isinstance(data["config_source"], str)
    assert len(data["config_source"]) > 0


def test_health_endpoint_app_name(client: TestClient) -> None:
    """Test that the health endpoint returns app_name from settings."""
    response = client.get("/health")
    data = response.json()

    assert isinstance(data["app_name"], str)
    assert len(data["app_name"]) > 0


def test_health_endpoint_version(client: TestClient) -> None:
    """Test that the health endpoint returns version from settings."""
    response = client.get("/health")
    data = response.json()

    assert isinstance(data["version"], str)
    assert len(data["version"]) > 0


def test_health_endpoint_with_settings_values(client: TestClient) -> None:
    """Test that health endpoint returns actual settings values."""
    from app.core.config import settings

    response = client.get("/health")
    data = response.json()

    assert data["config_source"] == settings.config_source
    assert data["app_name"] == settings.app_name
    assert data["version"] == settings.app_version


def test_health_endpoint_multiple_requests(client: TestClient) -> None:
    """Test that the health endpoint is idempotent (same response for multiple calls)."""
    response1 = client.get("/health")
    response2 = client.get("/health")
    response3 = client.get("/health")

    assert response1.status_code == status.HTTP_200_OK
    assert response2.status_code == status.HTTP_200_OK
    assert response3.status_code == status.HTTP_200_OK

    assert response1.json() == response2.json()
    assert response2.json() == response3.json()


def test_health_endpoint_no_query_params(client: TestClient) -> None:
    """Test that the health endpoint doesn't require query parameters."""
    response = client.get("/health")
    assert response.status_code == status.HTTP_200_OK


def test_health_endpoint_ignores_query_params(client: TestClient) -> None:
    """Test that the health endpoint ignores query parameters."""
    response = client.get("/health?foo=bar&baz=qux")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "healthy"


def test_health_endpoint_options_method(client: TestClient) -> None:
    """Test that OPTIONS method is allowed (CORS preflight)."""
    response = client.options("/health")
    assert response.status_code in [
        status.HTTP_200_OK,
        status.HTTP_405_METHOD_NOT_ALLOWED,
    ]  # 200 if CORS enabled, 405 if not


def test_health_endpoint_head_method(client: TestClient) -> None:
    """Test that HEAD method is not explicitly allowed (405 with TestClient)."""
    response = client.head("/health")

    assert (
        response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    )  # Method Not Allowed with TestClient


def test_health_endpoint_post_not_allowed(client: TestClient) -> None:
    """Test that POST method is not allowed on health endpoint."""
    response = client.post("/health")
    assert (
        response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    )  # Method Not Allowed


def test_health_endpoint_put_not_allowed(client: TestClient) -> None:
    """Test that PUT method is not allowed on health endpoint."""
    response = client.put("/health")
    assert (
        response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    )  # Method Not Allowed


def test_health_endpoint_delete_not_allowed(client: TestClient) -> None:
    """Test that DELETE method is not allowed on health endpoint."""
    response = client.delete("/health")
    assert (
        response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    )  # Method Not Allowed


def test_health_endpoint_patch_not_allowed(client: TestClient) -> None:
    """Test that PATCH method is not allowed on health endpoint."""
    response = client.patch("/health")
    assert (
        response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED
    )  # Method Not Allowed


def test_health_endpoint_response_time(client: TestClient) -> None:
    """Test that the health endpoint responds quickly."""
    import time

    start = time.time()
    response = client.get("/health")
    elapsed = time.time() - start

    assert response.status_code == status.HTTP_200_OK
    # Health endpoint should respond in less than 1 second
    assert elapsed < 1.0


def test_health_endpoint_complete_response(client: TestClient) -> None:
    """Test the complete response structure and values."""
    response = client.get("/health")

    assert response.status_code == status.HTTP_200_OK
    assert response.headers["content-type"] == "application/json"

    data = response.json()

    assert data == {
        "status": "healthy",
        "config_source": data["config_source"],  # Dynamic value
        "app_name": data["app_name"],  # From settings
        "version": data["version"],  # From settings
    }

    # Verify all values are non-empty strings
    assert isinstance(data["status"], str)
    assert data["status"]
    assert isinstance(data["config_source"], str)
    assert data["config_source"]
    assert isinstance(data["app_name"], str)
    assert data["app_name"]
    assert isinstance(data["version"], str)
    assert data["version"]
