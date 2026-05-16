from fastapi import FastAPI, UploadFile, Form, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from uuid import uuid4
import os
import shutil
import subprocess

# Initialize FastAPI app
app = FastAPI()

# Directory to store uploaded and processed files
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Helper functions
def run_ffmpeg_command(command):
    try:
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"FFmpeg command failed: {e}")

def save_file_to_disk(uploaded_file, destination_folder):
    file_id = str(uuid4())
    file_path = os.path.join(destination_folder, file_id + os.path.splitext(uploaded_file.filename)[1])
    with open(file_path, "wb") as f:
        shutil.copyfileobj(uploaded_file.file, f)
    return file_id, file_path

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
    return result.stdout

@app.post("/extract_audio_to_mp3")
async def extract_audio_to_mp3(file: UploadFile):
    file_id, input_path = save_file_to_disk(file, UPLOAD_DIR)
    output_path = os.path.join(OUTPUT_DIR, f"{file_id}.mp3")
    run_ffmpeg_command(["ffmpeg", "-i", input_path, "-vn", output_path])
    return {"file_id": file_id}

@app.get("/download/{file_id}")
async def download_file(file_id: str):
    file_path = os.path.join(OUTPUT_DIR, f"{file_id}")
    possible_extensions = [".mp3", ".wav", ".mp4", ".jpg", ".zip"]
    for ext in possible_extensions:
        if os.path.exists(file_path + ext):
            return FileResponse(file_path + ext)
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
            "/download/{file_id}": "Download processed file by file ID",
        }
    }
