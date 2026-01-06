import logging
import subprocess
import time
from typing import Any

import requests
from python_on_whales import DockerClient

logger = logging.getLogger(__name__)
if not logging.getLogger().handlers:
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )


def test_build_all_services(docker_client: DockerClient) -> None:
    """Test building all Docker services."""
    docker_client.compose.build()

    docker_client.image.list()  # Ensure images were created

    result = subprocess.run(
        ["docker", "image", "ls", "--format", "{{.Repository}}:{{.Tag}}"],
        capture_output=True,
        text=True,
    )
    full_image_names = result.stdout.strip().split("\n")
    logger.info("Available images: %s", full_image_names)

    api_image_found = any("todoappapitutorial-api" in name for name in full_image_names)
    assert api_image_found, "API image was not built successfully"


def test_mongodb_service_lifecycle(
    docker_client: DockerClient,
    wait_for_healthy_containers: Any,
) -> None:
    """Test MongoDB service up/down lifecycle."""
    docker_client.compose.up(services=["mongo"], detach=True)

    service_health = wait_for_healthy_containers(["mongo"], max_wait=120)
    assert service_health["mongo"], "MongoDB should be healthy"

    containers = docker_client.compose.ps()
    mongo_container = None
    for container in containers:
        if "mongo" in container.name:
            mongo_container = container
            break

    assert mongo_container is not None, "MongoDB container not found"
    assert mongo_container.state.status == "running", "MongoDB container is not running"

    docker_client.compose.stop(services=["mongo"])

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
    docker_client.compose.up(services=["redis"], detach=True)

    service_health = wait_for_healthy_containers(["redis"], max_wait=120)
    assert service_health["redis"], "Redis should be healthy"

    containers = docker_client.compose.ps()
    redis_container = None
    for container in containers:
        if "redis" in container.name:
            redis_container = container
            break

    assert redis_container is not None, "Redis container not found"
    assert redis_container.state.status == "running", "Redis container is not running"

    docker_client.compose.stop(services=["redis"])

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
    docker_client.compose.up(services=["mongo", "redis"], detach=True)

    service_health = wait_for_healthy_containers(["mongo", "redis"], max_wait=30)

    assert service_health["mongo"], "MongoDB should be healthy after startup"
    assert service_health["redis"], "Redis should be healthy after startup"


def test_api_health(docker_client: DockerClient) -> None:
    """Test the API health endpoint"""

    docker_client.compose.up(detach=True)

    try:
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
        docker_client.compose.down(volumes=True, remove_orphans=True)
