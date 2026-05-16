# ffmpeg-API v1.0.0 Release Notes

## Scope

Initial standalone Splat-I module release of Rodney's working FFmpeg FastAPI service, copied from gtgb-scripthost:~/HOLD/ffmpeg and packaged for Docker.

## Release Gates

- Python endpoint tests pass.
- Docker image builds successfully.
- Dockerized service starts and reports healthy.
- Container smoke tests exercise every public endpoint.
- Private GitHub repository is created and pushed.

## Endpoint Inventory

The release endpoint inventory is maintained in README.md and exposed at runtime by GET /endpoints.
