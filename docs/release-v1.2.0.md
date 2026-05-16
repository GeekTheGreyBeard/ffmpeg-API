# ffmpeg-API v1.2.0 Release Notes

## Scope

v1.2.0 adds a standalone MCP server image and Compose service while keeping the REST API as the stable media-processing contract.

## Added

- `mcp-server/` Python package using the official MCP SDK.
- `ffmpeg-mcp:1.2.0` Docker image.
- `ffmpeg-mcp` Compose service with Streamable HTTP transport at `/mcp`.
- MCP health route at `/health`.
- MCP tools for health, endpoint listing, conversion, probing, audio extraction, frame extraction, MP3 splitting, scrubbing, artifact metadata lookup, and artifact deletion.
- MCP unit tests for tool registration and API client delegation.

## Changed

- Service version is now `1.2.0`.
- Docker Compose now runs both `ffmpeg-api` and `ffmpeg-mcp`.
- Container smoke validation uses `ffmpeg-api:1.2.0`.

## Architecture

The MCP server is intentionally a separate process/container. It talks to `ffmpeg-api` over HTTP through `FFMPEG_API_BASE_URL`, so the API remains usable on its own and the MCP layer can be deployed, secured, scaled, or split independently.
