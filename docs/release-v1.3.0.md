# ffmpeg-API v1.3.0 Release Notes

v1.3.0 adds trusted local batch audio conversion for large server-side jobs where multipart upload/download loops are too slow or fragile.

## Added

- `POST /batch/convert-local` for recursive local audio conversion while preserving relative paths.
- `GET /jobs/{job_id}` for batch job status, totals, skipped files, failures, and per-file output paths.
- Batch options for input/output format, overwrite behavior, audio codec, audio bitrate, sample rate, and channel count.

## Changed

- Service version is now `1.3.0`.
- Docker Compose builds the API image as `ffmpeg-api:1.3.0`.

## Notes

- The local batch endpoint is intended for trusted deployments with mounted or host-local media paths.
- Existing upload/download endpoints remain unchanged.
