# ffmpeg-API

ffmpeg-API is a standalone Splat-I module that exposes common FFmpeg and FFprobe media operations through a FastAPI HTTP service. It is not a PatriciAI subproject.

## Project Links

- Obsidian documentation: OpenClaw/Projects/splatI/ffmpeg-API/
- Source origin: gtgb-scripthost:~/HOLD/ffmpeg
- Release target: v1.0.0 after container and endpoint tests pass

## Run Locally

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e .[test]
./launch.sh
```

The API listens on 0.0.0.0:${PORT:-8000}.

## Docker

```bash
docker build -t ffmpeg-api:1.0.0 .
docker run --rm -p 8000:8000 -v ffmpeg-api-data:/data ffmpeg-api:1.0.0
```

Runtime media paths can be overridden with:

- FFMPEG_API_UPLOAD_DIR
- FFMPEG_API_OUTPUT_DIR

## Endpoints

- GET /health - Return service health and version.
- GET /endpoints - Return the endpoint catalog.
- POST /convert_to_mp3 - Upload audio/video and convert to MP3. Returns file_id.
- POST /convert_to_wav - Upload audio/video and convert to WAV. Returns file_id.
- POST /convert_to_mp4 - Upload video and convert to MP4. Returns file_id.
- POST /convert_image_to_jpg - Upload an image and convert to JPG. Returns file_id.
- POST /extract_audio - Upload video and extract audio as WAV. Returns file_id.
- POST /extract_images - Upload video and extract frames into a ZIP archive. Returns file_id.
- POST /probe - Upload media and return FFprobe JSON metadata.
- POST /extract_audio_to_mp3 - Upload video and extract audio as MP3. Returns file_id.
- POST /split_mp3 - Upload MP3 and split into chunks no larger than approximately 23 MB. Returns chunk_file_ids.
- POST /scrubber - Upload MP3 and remove silence with FFmpeg silenceremove. Returns file_id and output_file.
- GET /download/{file_id} - Download the first generated artifact whose filename starts with file_id.

## Testing

```bash
pip install -e .[test]
pytest
```

Container release validation is:

```bash
scripts/container-smoke-test.sh
```
