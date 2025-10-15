"""
End-to-end tests for Docker Compose services using python-on-whales.
Tests all combinations of services: API, MongoDB, Redis, and all together.
"""

import logging
import time
from typing import Any

import requests
from python_on_whales import DockerClient

# Use standard logging for tests to avoid permission issues
logger = logging.getLogger(__name__)
# Configure basic logging if it hasn't been configured
if not logging.getLogger().handlers:
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )


def test_build_all_services(docker_client: DockerClient) -> None:
    """Test building all Docker services."""
    # Build all services
    docker_client.compose.build()

    # Verify images were created
    docker_client.image.list()  # Ensure images were created

    # Check if our API image exists (todoappapitutorial-api)
    # Let's get the full image names from docker directly, not just sha256
    import subprocess

    result = subprocess.run(
        ["docker", "image", "ls", "--format", "{{.Repository}}:{{.Tag}}"],
        capture_output=True,
        text=True,
    )
    full_image_names = result.stdout.strip().split("\n")
    logger.info("Available images: %s", full_image_names)

    # Check if todoappapitutorial-api image exists
    api_image_found = any("todoappapitutorial-api" in name for name in full_image_names)
    assert api_image_found, "API image was not built successfully"


def test_mongodb_service_lifecycle(
    docker_client: DockerClient,
    wait_for_healthy_containers: Any,
) -> None:
    """Test MongoDB service up/down lifecycle."""
    # Start MongoDB only
    docker_client.compose.up(services=["mongo"], detach=True)

    # Wait for MongoDB to be ready
    service_health = wait_for_healthy_containers(["mongo"], max_wait=120)
    assert service_health["mongo"], "MongoDB should be healthy"

    # Check if MongoDB container is running
    containers = docker_client.compose.ps()
    mongo_container = None
    for container in containers:
        if "mongo" in container.name:
            mongo_container = container
            break

    assert mongo_container is not None, "MongoDB container not found"
    assert mongo_container.state.status == "running", "MongoDB container is not running"

    # Stop MongoDB
    docker_client.compose.stop(services=["mongo"])

    # Verify it's stopped
    containers = docker_client.compose.ps()
    for container in containers:
        if "mongo" in container.name:
            assert container.state.status in ["exited", "stopped"], (
                "MongoDB should be stopped"
            )


def test_redis_service_lifecycle(
    docker_client: DockerClient, wait_for_healthy_containers: Any
) -> None:
    """Test Redis service up/down lifecycle."""
    # Start Redis only
    docker_client.compose.up(services=["redis"], detach=True)

    # Wait for Redis to be ready
    service_health = wait_for_healthy_containers(["redis"], max_wait=120)
    assert service_health["redis"], "Redis should be healthy"

    # Check if Redis container is running
    containers = docker_client.compose.ps()
    redis_container = None
    for container in containers:
        if "redis" in container.name:
            redis_container = container
            break

    assert redis_container is not None, "Redis container not found"
    assert redis_container.state.status == "running", "Redis container is not running"

    # Stop Redis
    docker_client.compose.stop(services=["redis"])

    # Verify it's stopped
    containers = docker_client.compose.ps()
    for container in containers:
        if "redis" in container.name:
            assert container.state.status in ["exited", "stopped"], (
                "Redis should be stopped"
            )


def test_databases_together(
    docker_client: DockerClient, wait_for_healthy_containers: Any
) -> None:
    """Test MongoDB and Redis services together."""
    # Start both databases
    docker_client.compose.up(services=["mongo", "redis"], detach=True)

    # Wait for services to be ready with health check polling
    service_health = wait_for_healthy_containers(["mongo", "redis"], max_wait=30)

    # Final health check
    assert service_health["mongo"], "MongoDB should be healthy after startup"
    assert service_health["redis"], "Redis should be healthy after startup"


def test_api_health(docker_client: DockerClient) -> None:
    """Test the API health endpoint"""

    # Start all services in detached mode
    docker_client.compose.up(detach=True)

    try:
        # Wait for API to be ready
        max_retries = 15
        retry_interval = 2
        for i in range(max_retries):
            try:
                logger.info(
                    "Attempt %d/%d to connect to API health endpoint...",
                    i + 1,
                    max_retries,
                )
                response = requests.get("http://localhost:8000/health", timeout=2)
                if response.status_code == 200:
                    # Test assertions
                    data = response.json()
                    assert data.get("status") == "healthy"
                    logger.info("✅ API health check passed: %s", data)
                    break
            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
            ) as e:
                logger.info(
                    "API not ready yet (%s), waiting %ss...",
                    e.__class__.__name__,
                    retry_interval,
                )
                time.sleep(retry_interval)
        else:
            raise AssertionError(
                f"API did not become available after {max_retries * retry_interval} seconds"
            )
    finally:
        # Always tear down services after the test
        docker_client.compose.down(volumes=True, remove_orphans=True)
