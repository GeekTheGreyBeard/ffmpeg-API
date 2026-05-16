# ffmpeg-mcp

ffmpeg-mcp is a standalone MCP adapter for ffmpeg-API. It exposes the media API as agent-friendly MCP tools while keeping FFmpeg processing behind the HTTP API service.

The default transport is Streamable HTTP at /mcp.

## Environment

- FFMPEG_API_BASE_URL - Base URL for ffmpeg-API. Defaults to http://ffmpeg-api:8000 in Docker Compose.
- FFMPEG_MCP_HOST - Bind host. Defaults to 0.0.0.0.
- FFMPEG_MCP_PORT - Bind port. Defaults to 8080.

## Tools

- health
- list_endpoints
- convert_media
- probe_media
- extract_audio
- extract_frames
- split_mp3
- scrub_audio
- get_artifact
- delete_artifact

