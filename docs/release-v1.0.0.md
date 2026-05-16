# ffmpeg-API v1.0.0 Release Notes

## Scope

Initial standalone Splat-I module release of the FFmpeg FastAPI service, packaged for Docker and Docker Compose.

## Release Gates

- Python endpoint tests pass: 12 passed.
- Docker image builds successfully: ffmpeg-api:1.0.0.
- Dockerized service starts and reports healthy.
- Container smoke tests exercise every public endpoint: passed.
- Private GitHub repository is created and pushed: https://github.com/GeekTheGreyBeard/ffmpeg-API.
- GitHub release is published: https://github.com/GeekTheGreyBeard/ffmpeg-API/releases/tag/v1.0.0.

## Endpoint Inventory

The release endpoint inventory is maintained in README.md and exposed at runtime by GET /endpoints.
