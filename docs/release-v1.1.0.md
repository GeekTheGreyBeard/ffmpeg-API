# ffmpeg-API v1.1.0 Release Notes

## Scope

v1.1.0 expands the API while keeping existing v1.0.0 convenience endpoints backward-compatible.

## Added

- `POST /convert` for generic media conversion with format, codec, bitrate, resolution, frame-rate, sample-rate, channel, and quality controls.
- Artifact metadata in processing responses, including filename, MIME type, size, operation, created timestamp, and `download_url`.
- Exact artifact metadata lookup with `GET /artifacts/{file_id}`.
- Exact artifact deletion with `DELETE /artifacts/{file_id}`.
- Exact metadata-backed downloads, replacing prefix-only filesystem search.

## Changed

- Service version is now `1.1.0`.
- Docker Compose image tag is now `ffmpeg-api:1.1.0`.
- Container smoke validation now covers `/convert`, artifact metadata lookup, and artifact deletion.

## Compatibility

- Existing processing endpoints still return `file_id`.
- Existing `/download/{file_id}` URLs continue to work for newly generated artifacts.
- New response metadata is additive for existing endpoint clients.
