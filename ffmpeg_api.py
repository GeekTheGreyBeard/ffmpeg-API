import json
import mimetypes
import os
import shutil
import subprocess
import time
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

app = FastAPI(
    title="Splat-I FFmpeg API",
    version="1.2.0",
    description="Standalone Splat-I module exposing common FFmpeg media operations over HTTP.",
)

UPLOAD_DIR = Path(os.getenv("FFMPEG_API_UPLOAD_DIR", "uploads"))
OUTPUT_DIR = Path(os.getenv("FFMPEG_API_OUTPUT_DIR", "outputs"))
METADATA_DIR = OUTPUT_DIR / ".metadata"

for directory in (UPLOAD_DIR, OUTPUT_DIR, METADATA_DIR):
    directory.mkdir(parents=True, exist_ok=True)

ALLOWED_GENERIC_FORMATS = {
    "aac",
    "flac",
    "gif",
    "jpg",
    "jpeg",
    "m4a",
    "mkv",
    "mov",
    "mp3",
    "mp4",
    "ogg",
    "opus",
    "png",
    "wav",
    "webm",
    "webp",
}

ALLOWED_VIDEO_CODECS = {"copy", "libx264", "libx265", "mpeg4", "libvpx-vp9"}
ALLOWED_AUDIO_CODECS = {"copy", "aac", "libmp3lame", "libopus", "pcm_s16le", "flac"}
ALLOWED_VIDEO_QUALITIES = {"low", "medium", "high"}

VIDEO_QUALITY_ARGS = {
    "low": ["-crf", "30", "-preset", "veryfast"],
    "medium": ["-crf", "23", "-preset", "medium"],
    "high": ["-crf", "18", "-preset", "slow"],
}


def run_command(command):
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        detail = e.stderr.strip() or e.stdout.strip() or str(e)
        raise HTTPException(status_code=500, detail=f"FFmpeg command failed: {detail}")


def run_probe(input_path):
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-print_format",
            "json",
            str(input_path),
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail="Error probing file")
    return json.loads(result.stdout)


def save_file_to_disk(uploaded_file, destination_folder):
    file_id = str(uuid4())
    suffix = Path(uploaded_file.filename or "").suffix
    file_path = Path(destination_folder) / f"{file_id}{suffix}"
    with file_path.open("wb") as f:
        shutil.copyfileobj(uploaded_file.file, f)
    return file_id, file_path


def artifact_metadata_path(file_id):
    return METADATA_DIR / f"{file_id}.json"


def write_artifact_metadata(file_id, path, operation, source_file_id=None, extra=None):
    path = Path(path)
    artifact = {
        "file_id": file_id,
        "source_file_id": source_file_id,
        "operation": operation,
        "filename": path.name,
        "path": str(path.relative_to(OUTPUT_DIR)),
        "size_bytes": path.stat().st_size if path.exists() else 0,
        "mime_type": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
        "download_url": f"/download/{file_id}",
        "created_at": int(time.time()),
    }
    if extra:
        artifact.update(extra)
    artifact_metadata_path(file_id).write_text(json.dumps(artifact, indent=2), encoding="utf-8")
    return artifact


def read_artifact_metadata(file_id):
    metadata_path = artifact_metadata_path(file_id)
    if not metadata_path.exists():
        raise HTTPException(status_code=404, detail="Artifact not found")
    return json.loads(metadata_path.read_text(encoding="utf-8"))


def resolve_artifact_path(file_id):
    metadata = read_artifact_metadata(file_id)
    path = (OUTPUT_DIR / metadata["path"]).resolve()
    output_root = OUTPUT_DIR.resolve()
    if output_root not in path.parents and path != output_root:
        raise HTTPException(status_code=404, detail="Artifact not found")
    if not path.exists() or not path.is_file():
        raise HTTPException(status_code=404, detail="Artifact file not found")
    return metadata, path


def create_artifact_response(file_id, output_path, operation, source_file_id=None, extra=None):
    artifact = write_artifact_metadata(file_id, output_path, operation, source_file_id, extra)
    return {
        "file_id": file_id,
        "download_url": artifact["download_url"],
        "artifact": artifact,
    }


def validate_choice(name, value, allowed):
    if value is not None and value not in allowed:
        allowed_values = ", ".join(sorted(allowed))
        raise HTTPException(status_code=400, detail=f"{name} must be one of: {allowed_values}")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ffmpeg-API", "version": app.version}


@app.post("/convert")
async def convert(
    file: UploadFile,
    format: str = Form(...),
    video_codec: str | None = Form(None),
    audio_codec: str | None = Form(None),
    video_bitrate: str | None = Form(None),
    audio_bitrate: str | None = Form(None),
    resolution: str | None = Form(None),
    frame_rate: int | None = Form(None),
    sample_rate: int | None = Form(None),
    audio_channels: int | None = Form(None),
    quality: str | None = Form(None),
):
    output_format = format.lower().lstrip(".")
    validate_choice("format", output_format, ALLOWED_GENERIC_FORMATS)
    validate_choice("video_codec", video_codec, ALLOWED_VIDEO_CODECS)
    validate_choice("audio_codec", audio_codec, ALLOWED_AUDIO_CODECS)
    validate_choice("quality", quality, ALLOWED_VIDEO_QUALITIES)

    if frame_rate is not None and not 1 <= frame_rate <= 240:
        raise HTTPException(status_code=400, detail="frame_rate must be between 1 and 240")
    if sample_rate is not None and sample_rate not in {8000, 11025, 16000, 22050, 24000, 32000, 44100, 48000, 96000}:
        raise HTTPException(status_code=400, detail="sample_rate is not supported")
    if audio_channels is not None and audio_channels not in {1, 2, 6, 8}:
        raise HTTPException(status_code=400, detail="audio_channels must be 1, 2, 6, or 8")
    if resolution is not None and not resolution.replace("x", "").isdigit():
        raise HTTPException(status_code=400, detail="resolution must use WIDTHxHEIGHT format")

    file_id, input_path = save_file_to_disk(file, UPLOAD_DIR)
    output_path = OUTPUT_DIR / f"{file_id}.{output_format}"

    command = ["ffmpeg", "-i", str(input_path)]
    if video_codec:
        command.extend(["-c:v", video_codec])
    if audio_codec:
        command.extend(["-c:a", audio_codec])
    if video_bitrate:
        command.extend(["-b:v", video_bitrate])
    if audio_bitrate:
        command.extend(["-b:a", audio_bitrate])
    if resolution:
        command.extend(["-s", resolution])
    if frame_rate is not None:
        command.extend(["-r", str(frame_rate)])
    if sample_rate is not None:
        command.extend(["-ar", str(sample_rate)])
    if audio_channels is not None:
        command.extend(["-ac", str(audio_channels)])
    if quality:
        command.extend(VIDEO_QUALITY_ARGS[quality])
    command.append(str(output_path))

    run_command(command)
    return create_artifact_response(
        file_id,
        output_path,
        "convert",
        source_file_id=file_id,
        extra={
            "format": output_format,
            "video_codec": video_codec,
            "audio_codec": audio_codec,
            "video_bitrate": video_bitrate,
            "audio_bitrate": audio_bitrate,
            "resolution": resolution,
            "frame_rate": frame_rate,
            "sample_rate": sample_rate,
            "audio_channels": audio_channels,
            "quality": quality,
        },
    )


@app.post("/convert_to_mp3")
async def convert_to_mp3(file: UploadFile):
    file_id, input_path = save_file_to_disk(file, UPLOAD_DIR)
    output_path = OUTPUT_DIR / f"{file_id}.mp3"
    run_command(["ffmpeg", "-i", str(input_path), str(output_path)])
    return create_artifact_response(file_id, output_path, "convert_to_mp3", file_id)


@app.post("/convert_to_wav")
async def convert_to_wav(file: UploadFile):
    file_id, input_path = save_file_to_disk(file, UPLOAD_DIR)
    output_path = OUTPUT_DIR / f"{file_id}.wav"
    run_command(["ffmpeg", "-i", str(input_path), str(output_path)])
    return create_artifact_response(file_id, output_path, "convert_to_wav", file_id)


@app.post("/convert_to_mp4")
async def convert_to_mp4(file: UploadFile):
    file_id, input_path = save_file_to_disk(file, UPLOAD_DIR)
    output_path = OUTPUT_DIR / f"{file_id}.mp4"
    run_command(["ffmpeg", "-i", str(input_path), str(output_path)])
    return create_artifact_response(file_id, output_path, "convert_to_mp4", file_id)


@app.post("/convert_image_to_jpg")
async def convert_image_to_jpg(file: UploadFile):
    file_id, input_path = save_file_to_disk(file, UPLOAD_DIR)
    output_path = OUTPUT_DIR / f"{file_id}.jpg"
    run_command(["ffmpeg", "-i", str(input_path), str(output_path)])
    return create_artifact_response(file_id, output_path, "convert_image_to_jpg", file_id)


@app.post("/extract_audio")
async def extract_audio(file: UploadFile):
    file_id, input_path = save_file_to_disk(file, UPLOAD_DIR)
    output_path = OUTPUT_DIR / f"{file_id}.wav"
    run_command(["ffmpeg", "-i", str(input_path), "-vn", str(output_path)])
    return create_artifact_response(file_id, output_path, "extract_audio", file_id)


@app.post("/extract_images")
async def extract_images(file: UploadFile):
    file_id, input_path = save_file_to_disk(file, UPLOAD_DIR)
    images_dir = OUTPUT_DIR / file_id
    images_dir.mkdir(exist_ok=True)
    run_command(["ffmpeg", "-i", str(input_path), str(images_dir / "%04d.jpg")])
    zip_path = OUTPUT_DIR / f"{file_id}.zip"
    shutil.make_archive(base_name=str(zip_path.with_suffix("")), format="zip", root_dir=images_dir)
    return create_artifact_response(file_id, zip_path, "extract_images", file_id)


@app.post("/probe")
async def probe(file: UploadFile):
    _, input_path = save_file_to_disk(file, UPLOAD_DIR)
    return run_probe(input_path)


@app.post("/extract_audio_to_mp3")
async def extract_audio_to_mp3(file: UploadFile):
    file_id, input_path = save_file_to_disk(file, UPLOAD_DIR)
    output_path = OUTPUT_DIR / f"{file_id}.mp3"
    run_command(["ffmpeg", "-i", str(input_path), "-vn", str(output_path)])
    return create_artifact_response(file_id, output_path, "extract_audio_to_mp3", file_id)


@app.post("/split_mp3")
async def split_mp3(file: UploadFile):
    file_id, input_path = save_file_to_disk(file, UPLOAD_DIR)
    output_dir = OUTPUT_DIR / file_id
    output_dir.mkdir(exist_ok=True)

    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(input_path),
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise HTTPException(status_code=500, detail="Error getting file duration")

    duration = float(result.stdout.strip())
    segment_duration = 23 * 1024 * 1024 * 8 / (128 * 1000)

    chunks = []
    start_time = 0
    index = 1

    while start_time < duration:
        chunk_file_id = f"{file_id}_part{index}"
        chunk_path = output_dir / f"{chunk_file_id}.mp3"

        run_command(
            [
                "ffmpeg",
                "-i",
                str(input_path),
                "-ss",
                str(start_time),
                "-t",
                str(segment_duration),
                "-c",
                "copy",
                str(chunk_path),
            ]
        )

        chunks.append(write_artifact_metadata(chunk_file_id, chunk_path, "split_mp3", file_id))
        start_time += segment_duration
        index += 1

    return {"file_id": file_id, "chunk_file_ids": [chunk["file_id"] for chunk in chunks], "chunks": chunks}


@app.post("/scrubber")
async def scrubber(file: UploadFile):
    file_id, input_path = save_file_to_disk(file, UPLOAD_DIR)
    output_path = OUTPUT_DIR / f"{file_id}_scrubbed.mp3"
    run_command(["ffmpeg", "-i", str(input_path), "-af", "silenceremove=1:0:-50dB", str(output_path)])
    response = create_artifact_response(file_id, output_path, "scrubber", file_id)
    response["output_file"] = output_path.name
    return response


@app.get("/artifacts/{file_id}")
async def get_artifact(file_id: str):
    return read_artifact_metadata(file_id)


@app.delete("/artifacts/{file_id}")
async def delete_artifact(file_id: str):
    metadata, path = resolve_artifact_path(file_id)
    path.unlink()
    artifact_metadata_path(file_id).unlink(missing_ok=True)
    return {"deleted": True, "file_id": file_id, "artifact": metadata}


@app.get("/download/{file_id}")
async def download_file(file_id: str):
    metadata, path = resolve_artifact_path(file_id)
    return FileResponse(path, media_type=metadata["mime_type"], filename=metadata["filename"])


@app.get("/endpoints")
async def list_endpoints():
    return {
        "endpoints": {
            "/convert": "Convert uploaded media to a requested format with optional codec/bitrate/resolution parameters",
            "/convert_to_mp3": "Convert audio to MP3 format",
            "/convert_to_wav": "Convert audio to WAV format",
            "/convert_to_mp4": "Convert video to MP4 format",
            "/convert_image_to_jpg": "Convert image to JPG format",
            "/extract_audio": "Extract audio as WAV from video",
            "/extract_images": "Extract images from video as a ZIP file",
            "/probe": "Get metadata of the media file",
            "/extract_audio_to_mp3": "Extract audio as MP3 from video",
            "/split_mp3": "Split an MP3 file into chunks no larger than 23MB each",
            "/scrubber": "Remove silence from an MP3 file using silenceremove filter",
            "/artifacts/{file_id}": "Get or delete generated artifact metadata by file ID",
            "/download/{file_id}": "Download processed file by exact file ID",
            "/health": "Return container/service health status",
        }
    }
