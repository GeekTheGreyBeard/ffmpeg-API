import json
import os
import shutil
import subprocess
from uuid import uuid4

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse

app = FastAPI(
    title="Splat-I FFmpeg API",
    version="1.0.0",
    description="Standalone Splat-I module exposing common FFmpeg media operations over HTTP.",
)

UPLOAD_DIR = os.getenv("FFMPEG_API_UPLOAD_DIR", "uploads")
OUTPUT_DIR = os.getenv("FFMPEG_API_OUTPUT_DIR", "outputs")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

def run_ffmpeg_command(command):
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        detail = e.stderr.strip() or e.stdout.strip() or str(e)
        raise HTTPException(status_code=500, detail=f"FFmpeg command failed: {detail}")


def save_file_to_disk(uploaded_file, destination_folder):
    file_id = str(uuid4())
    file_path = os.path.join(destination_folder, file_id + os.path.splitext(uploaded_file.filename)[1])
    with open(file_path, "wb") as f:
        shutil.copyfileobj(uploaded_file.file, f)
    return file_id, file_path


@app.get("/health")
async def health():
    return {"status": "ok", "service": "ffmpeg-API", "version": app.version}

@app.post("/convert_to_mp3")
async def convert_to_mp3(file: UploadFile):
    file_id, input_path = save_file_to_disk(file, UPLOAD_DIR)
    output_path = os.path.join(OUTPUT_DIR, f"{file_id}.mp3")
    run_ffmpeg_command(["ffmpeg", "-i", input_path, output_path])
    return {"file_id": file_id}

@app.post("/convert_to_wav")
async def convert_to_wav(file: UploadFile):
    file_id, input_path = save_file_to_disk(file, UPLOAD_DIR)
    output_path = os.path.join(OUTPUT_DIR, f"{file_id}.wav")
    run_ffmpeg_command(["ffmpeg", "-i", input_path, output_path])
    return {"file_id": file_id}

@app.post("/convert_to_mp4")
async def convert_to_mp4(file: UploadFile):
    file_id, input_path = save_file_to_disk(file, UPLOAD_DIR)
    output_path = os.path.join(OUTPUT_DIR, f"{file_id}.mp4")
    run_ffmpeg_command(["ffmpeg", "-i", input_path, output_path])
    return {"file_id": file_id}

@app.post("/convert_image_to_jpg")
async def convert_image_to_jpg(file: UploadFile):
    file_id, input_path = save_file_to_disk(file, UPLOAD_DIR)
    output_path = os.path.join(OUTPUT_DIR, f"{file_id}.jpg")
    run_ffmpeg_command(["ffmpeg", "-i", input_path, output_path])
    return {"file_id": file_id}

@app.post("/extract_audio")
async def extract_audio(file: UploadFile):
    file_id, input_path = save_file_to_disk(file, UPLOAD_DIR)
    output_path = os.path.join(OUTPUT_DIR, f"{file_id}.wav")
    run_ffmpeg_command(["ffmpeg", "-i", input_path, "-vn", output_path])
    return {"file_id": file_id}

@app.post("/extract_images")
async def extract_images(file: UploadFile):
    file_id, input_path = save_file_to_disk(file, UPLOAD_DIR)
    images_dir = os.path.join(OUTPUT_DIR, file_id)
    os.makedirs(images_dir, exist_ok=True)
    run_ffmpeg_command(["ffmpeg", "-i", input_path, os.path.join(images_dir, "%04d.jpg")])
    zip_path = os.path.join(OUTPUT_DIR, f"{file_id}.zip")
    shutil.make_archive(base_name=zip_path[:-4], format="zip", root_dir=images_dir)
    return {"file_id": file_id}

@app.post("/probe")
async def probe(file: UploadFile):
    file_id, input_path = save_file_to_disk(file, UPLOAD_DIR)
    result = subprocess.run(["ffprobe", "-v", "error", "-show_format", "-show_streams", "-print_format", "json", input_path], capture_output=True, text=True)
    if result.returncode != 0:
        raise HTTPException(status_code=500, detail="Error probing file")
    return json.loads(result.stdout)

@app.post("/extract_audio_to_mp3")
async def extract_audio_to_mp3(file: UploadFile):
    file_id, input_path = save_file_to_disk(file, UPLOAD_DIR)
    output_path = os.path.join(OUTPUT_DIR, f"{file_id}.mp3")
    run_ffmpeg_command(["ffmpeg", "-i", input_path, "-vn", output_path])
    return {"file_id": file_id}

@app.post("/split_mp3")
async def split_mp3(file: UploadFile):
    file_id, input_path = save_file_to_disk(file, UPLOAD_DIR)
    output_dir = os.path.join(OUTPUT_DIR, file_id)
    os.makedirs(output_dir, exist_ok=True)

    # Get the duration of the file
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", input_path
    ], capture_output=True, text=True)

    if result.returncode != 0:
        raise HTTPException(status_code=500, detail="Error getting file duration")

    duration = float(result.stdout.strip())
    segment_duration = 23 * 1024 * 1024 * 8 / (128 * 1000)  # 23MB with a 128kbps bitrate

    chunk_file_ids = []
    start_time = 0
    index = 1

    while start_time < duration:
        chunk_file_id = f"{file_id}_part{index}"
        chunk_path = os.path.join(output_dir, f"{chunk_file_id}.mp3")

        run_ffmpeg_command([
            "ffmpeg", "-i", input_path, "-ss", str(start_time), "-t", str(segment_duration), "-c", "copy", chunk_path
        ])

        chunk_file_ids.append(chunk_file_id)
        start_time += segment_duration
        index += 1

    return {"chunk_file_ids": chunk_file_ids}

@app.post("/scrubber")
async def scrubber(file: UploadFile):
    file_id, input_path = save_file_to_disk(file, UPLOAD_DIR)
    output_path = os.path.join(OUTPUT_DIR, f"{file_id}_scrubbed.mp3")
    run_ffmpeg_command(["ffmpeg", "-i", input_path, "-af", "silenceremove=1:0:-50dB", output_path])
    return {"file_id": file_id, "output_file": f"{file_id}_scrubbed.mp3"}

@app.get("/download/{file_id}")
async def download_file(file_id: str):
    # Search for the file in the OUTPUT_DIR and its subdirectories
    for root, _, files in os.walk(OUTPUT_DIR):
        for file in files:
            if file.startswith(file_id):
                file_path = os.path.join(root, file)
                return FileResponse(file_path)
    raise HTTPException(status_code=404, detail="File not found")

@app.get("/endpoints")
async def list_endpoints():
    return {
        "endpoints": {
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
            "/download/{file_id}": "Download processed file by file ID",
            "/health": "Return container/service health status",
        }
    }
