"""
Pytest configuration and shared fixtures for Docker Compose e2e tests.
"""

# Additional wait to ensure API is fully initialized and ready for requests
import contextlib
import logging
import tempfile
import time
from collections.abc import Callable, Generator
from pathlib import Path
from typing import Any
from unittest.mock import patch

# Additional wait to ensure API is fully initialized and ready for requests
import pytest
import requests
from python_on_whales import DockerClient

from app.core.config import settings

# Import logger setup function
from app.core.logging import get_logger

# Initialize logger at test session start with a temporary log file
with patch.object(settings, "log_file", tempfile.mktemp(suffix=".log")):
    logger = get_logger(__name__)


@pytest.fixture(scope="session")
def docker_client() -> DockerClient:
    """Provide Docker client with project directory context."""
    project_root = Path(__file__).parent.parent
    return DockerClient(compose_files=[project_root / "docker-compose.yml"])


@pytest.fixture(autouse=True)
def docker_cleanup(docker_client: DockerClient) -> Generator[None, None, None]:
    """Ensure clean state before and after each test."""
    # Cleanup before test
    with contextlib.suppress(Exception):
        docker_client.compose.down(volumes=True, remove_orphans=True)

    yield

    # Cleanup after test
    with contextlib.suppress(Exception):
        docker_client.compose.down(volumes=True, remove_orphans=True)


@pytest.fixture(scope="session")
def wait_for_healthy_containers(
    docker_client: DockerClient,
) -> Callable[[list[str], int], dict[str, bool]]:
    """Helper fixture to wait for containers to become healthy."""

    def _wait_for_healthy(services: list[str], max_wait: int = 90) -> dict[str, bool]:
        """
        Wait for specified services to become healthy.

        Args:
            services: List of service names to wait for
            max_wait: Maximum time to wait in seconds

        Returns:
            Dict mapping service names to their health status
        """
        wait_interval = 5
        waited = 0
        service_health = dict.fromkeys(services, False)

        while waited < max_wait:
            time.sleep(wait_interval)
            waited += wait_interval

            try:
                containers = docker_client.compose.ps()

                # Check each service against containers
                for service in services:
                    # Skip if already found healthy
                    if service_health[service]:
                        continue

                    # Map service names to container name patterns
                    service_patterns = {
                        "mongo": ["mongo"],
                        "redis": ["redis"],
                        "api": ["api"],
                    }

                    for container in containers:
                        # Check if container matches the service
                        is_target_service = False
                        if service in service_patterns:
                            for pattern in service_patterns[service]:
                                if pattern in container.name.lower():
                                    is_target_service = True
                                    break
                        else:
                            # Fallback to original logic for unknown services
                            is_target_service = service in container.name.lower()

                        if is_target_service and container.state.status == "running":
                            # Check health status properly - container.state.health is an object with a status attribute
                            health_obj = container.state.health
                            is_healthy = (
                                health_obj is not None
                                and hasattr(health_obj, "status")
                                and str(health_obj.status) == "healthy"
                            )
                            service_health[service] = is_healthy
                            logger.debug(
                                f"service_health after assignment: {service_health}"
                            )
                            if is_healthy:
                                logger.info(
                                    f"✅ {service} ({container.name}) is healthy"
                                )
                                break  # Found healthy service, move to next service

                            logger.debug(
                                f"⏳ {service} ({container.name}) status: {container.state.status}, health: {container.state.health}"
                            )

                # Check if all services are healthy
                if all(service_health.values()):
                    logger.info(f"✅ All services healthy: {service_health}")
                    break

                logger.info(
                    f"Waiting for health checks... ({waited}/{max_wait}s) - Status: {service_health}"
                )

            except Exception as e:
                logger.error(f"Error checking containers: {e}")

        return service_health

    return _wait_for_healthy


@pytest.fixture
def api_base_url() -> str:
    """Base URL for API endpoints."""
    return "http://localhost:8000"


@pytest.fixture(scope="session")
def build(
    docker_client: DockerClient,
    wait_for_healthy_containers: Callable[[list[str], int], dict[str, bool]],
) -> Generator[None, None, None]:
    """Build and start Docker Compose services and wait for them to be healthy."""
    # Start all services in detached mode
    docker_client.compose.up(detach=True)

    # Wait for services to become healthy (pass 90 as positional argument)
    healthy = wait_for_healthy_containers(["mongo", "redis", "api"], 90)
    assert all(healthy.values()), f"Not all services are healthy: {healthy}"

    # Additional wait to ensure API is fully initialized and ready for requests
    import time

    # Try to connect to the health endpoint for up to 20 seconds
    max_retries = 10
    retry_interval = 2
    for i in range(max_retries):
        try:
            logger.info(f"Checking API availability (attempt {i + 1}/{max_retries})...")
            response = requests.get("http://localhost:8000/health", timeout=2)
            if response.status_code == 200:
                logger.info(f"✅ API is fully available: {response.json()}")
                break
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            logger.warning(f"API not yet available, waiting {retry_interval}s...")
            time.sleep(retry_interval)

    # Now yield control to the tests
    yield

    # Tear down services after tests
    docker_client.compose.down(volumes=True, remove_orphans=True)
