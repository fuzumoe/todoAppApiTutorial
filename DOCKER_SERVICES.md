# Docker Services Setup

## Running MongoDB and Redis for Development

To run MongoDB and Redis services independently (without the API):

```bash
docker-compose -f docker-compose.services.yml up -d mongo redis
```

This uses the dedicated `docker-compose.services.yml` file which:
- Starts MongoDB on port 27017
- Starts Redis on port 6379
- Configures default credentials from `.env` or hardcoded defaults
- Enables health checks
- Keeps containers running independently

## Stopping Services

```bash
docker-compose -f docker-compose.services.yml down
```

## Running the Full Stack (API + MongoDB + Redis)

```bash
docker-compose up -d
```

This runs everything including the API service and will depend on MongoDB and Redis being healthy.

## Common Issues

### Containers shut down unexpectedly

If containers are shutting down when running `docker-compose up -d mongo redis` (without specifying a file), you may need to specify the services compose file or use the full compose file with `up -d` to run everything.

### Connection refused

Ensure services are healthy before running tests:
```bash
docker ps | grep -E "mongo|redis"
```

Look for `(healthy)` status. If showing `(health: starting)`, wait a few seconds for health checks to pass.
