# ffmpeg-API

ffmpeg-API is a small FastAPI service for running common FFmpeg and FFprobe media operations over HTTP.

It is useful when an app, workflow, or automation pipeline needs media conversion without embedding FFmpeg command handling into every client. Upload a file, receive a generated `file_id`, then download the processed artifact from the API.

The Docker Compose stack also includes `ffmpeg-mcp`, a standalone MCP server that exposes the API as agent-friendly tools over Streamable HTTP.

## What It Does

- Converts audio and video to MP3, WAV, or MP4.
- Converts uploaded media through a generic `/convert` endpoint with format, codec, bitrate, resolution, frame-rate, sample-rate, channel, and quality options.
- Converts images to JPG.
- Extracts audio from video as WAV or MP3.
- Extracts video frames into a ZIP archive.
- Probes media files with FFprobe and returns JSON metadata.
- Batch converts trusted local audio directories while preserving relative paths and tracking job status.
- Splits MP3 files into approximately 23 MB chunks.
- Removes silence from MP3/audio files with FFmpeg's `silenceremove` filter.

## Requirements

For Docker Compose:

- Docker
- Docker Compose

For local Python development:

- Python 3.12 or newer
- FFmpeg and FFprobe available on `PATH`

The Docker image installs FFmpeg for you.

## Quick Start

```bash
cp .env.example .env
docker compose up -d --build
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:18003/health
```

By default, the service listens on port `8000`. Set `FFMPEG_API_PORT` in `.env` to use a different host port.

Interactive OpenAPI docs are available at:

```text
http://127.0.0.1:8000/docs
```

The MCP server is available at:

```text
http://127.0.0.1:18003/mcp
```

To stop the stack:

```bash
docker compose down
```

Processed uploads and outputs are stored in the named Docker volume `ffmpeg-api-data`.

## Docker

```bash
docker build -t ffmpeg-api:1.3.0 .
docker run --rm -p 8000:8000 -v ffmpeg-api-data:/data ffmpeg-api:1.3.0
```

Runtime media paths can be overridden with:

- `FFMPEG_API_UPLOAD_DIR` - where incoming uploads are stored.
- `FFMPEG_API_OUTPUT_DIR` - where generated artifacts are stored.

## Local Development

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .[test]
./launch.sh
```

By default, the local service listens on port `8000`. Set `PORT` to override it.

## API

Most `POST` endpoints accept `multipart/form-data` with a file field named `file`. Processing endpoints return a generated `file_id`, artifact metadata, and a `download_url`; use `GET /download/{file_id}` to retrieve the generated artifact.

- `GET /health` - Return service health and version.
- `GET /endpoints` - Return the endpoint catalog.
- `POST /convert` - Convert uploaded media to a requested format with optional codec/bitrate/resolution controls.
- `POST /convert_to_mp3` - Convert uploaded audio/video to MP3.
- `POST /convert_to_wav` - Convert uploaded audio/video to WAV.
- `POST /convert_to_mp4` - Convert uploaded video/media to MP4.
- `POST /convert_image_to_jpg` - Convert an uploaded image to JPG.
- `POST /extract_audio` - Extract audio from uploaded video as WAV.
- `POST /extract_images` - Extract video frames into a ZIP archive.
- `POST /probe` - Return FFprobe JSON metadata for uploaded media.
- `POST /extract_audio_to_mp3` - Extract audio from uploaded video/media as MP3.
- `POST /batch/convert-local` - Batch convert trusted local audio files while preserving relative paths.
- `GET /jobs/{job_id}` - Return batch job status and per-file conversion results.
- `POST /split_mp3` - Split an uploaded MP3 into approximately 23 MB chunks.
- `POST /scrubber` - Remove silence from uploaded MP3/audio.
- `GET /artifacts/{file_id}` - Return metadata for a generated artifact.
- `DELETE /artifacts/{file_id}` - Delete a generated artifact and its metadata.
- `GET /download/{file_id}` - Download a generated artifact by file ID.

Example:

```bash
curl -X POST -F "file=@sample.wav" http://127.0.0.1:8000/convert_to_mp3
curl -o output.mp3 http://127.0.0.1:8000/download/<file_id>
```

Generic conversion example:

```bash
curl -X POST \
  -F "file=@sample.mov" \
  -F "format=mp4" \
  -F "video_codec=libx264" \
  -F "audio_codec=aac" \
  -F "quality=medium" \
  http://127.0.0.1:8000/convert
```

Replace `<file_id>` with the value returned by the processing endpoint.

Trusted local batch conversion example:

```bash
curl -X POST \
  -F "source_dir=/data/source-wav" \
  -F "output_dir=/data/output-mp3" \
  -F "input_format=wav" \
  -F "output_format=mp3" \
  -F "audio_bitrate=128k" \
  -F "recursive=true" \
  http://127.0.0.1:8000/batch/convert-local

curl http://127.0.0.1:8000/jobs/<job_id>
```

The batch endpoint is intended for trusted deployments where source and destination directories are mounted into the API container or available on the host for local development.

## MCP Server

The Compose stack builds a second image, `ffmpeg-mcp:1.2.0`, from `mcp-server/`.

The MCP server is intentionally standalone. It does not import the FastAPI app directly; it calls `ffmpeg-api` over HTTP using `FFMPEG_API_BASE_URL`. In Docker Compose, that URL is `http://ffmpeg-api:8000`.

Available MCP tools:

- `health`
- `list_endpoints`
- `convert_media`
- `probe_media`
- `extract_audio`
- `extract_frames`
- `split_mp3`
- `scrub_audio`
- `get_artifact`
- `delete_artifact`

For remote clients, media can be passed as base64 content. For trusted local/container-mounted use, tools also accept a `file_path`.


## Testing

```bash
pip install -e .[test]
pytest
```

Container release validation:

```bash
scripts/container-smoke-test.sh
```

The smoke test builds the Docker image, starts the API, generates small media fixtures, exercises every public endpoint, verifies downloads, and checks missing-file handling.
