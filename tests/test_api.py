import json
import shutil
import subprocess
import zipfile
from pathlib import Path

import pytest


pytestmark = pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="ffmpeg and ffprobe are required for API media tests",
)


def run_media_command(args):
    result = subprocess.run(
        args,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"Command failed: {' '.join(args)}\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )


def ffprobe_json(path):
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_format",
            "-show_streams",
            "-print_format",
            "json",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def make_wav(path):
    run_media_command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=440:duration=0.35",
            "-ar",
            "8000",
            "-ac",
            "1",
            str(path),
        ]
    )
    return path


def make_mp3(path):
    run_media_command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=550:duration=0.35",
            "-b:a",
            "64k",
            str(path),
        ]
    )
    return path


def make_mp3_with_leading_silence(path):
    run_media_command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "anullsrc=r=8000:cl=mono:d=0.15",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=660:duration=0.35:r=8000",
            "-filter_complex",
            "[0:a][1:a]concat=n=2:v=0:a=1",
            "-b:a",
            "64k",
            str(path),
        ]
    )
    return path


def make_mp4(path):
    run_media_command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc=size=32x32:rate=1:duration=1",
            "-f",
            "lavfi",
            "-i",
            "sine=frequency=770:duration=1",
            "-shortest",
            "-pix_fmt",
            "yuv420p",
            "-c:v",
            "mpeg4",
            "-c:a",
            "aac",
            str(path),
        ]
    )
    return path


def make_avi(path):
    run_media_command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "testsrc=size=32x32:rate=1:duration=1",
            "-pix_fmt",
            "yuv420p",
            "-c:v",
            "mpeg4",
            str(path),
        ]
    )
    return path


def make_png(path):
    run_media_command(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "lavfi",
            "-i",
            "color=c=red:s=16x16",
            "-frames:v",
            "1",
            str(path),
        ]
    )
    return path


def upload(client, endpoint, path, content_type):
    with Path(path).open("rb") as media_file:
        return client.post(
            endpoint,
            files={"file": (Path(path).name, media_file, content_type)},
        )


def output_path(api_module, file_id, extension):
    return Path(api_module.OUTPUT_DIR) / f"{file_id}.{extension}"


def assert_downloads(client, file_id):
    response = client.get(f"/download/{file_id}")
    assert response.status_code == 200
    assert response.content
    return response


def assert_has_stream(path, stream_type):
    metadata = ffprobe_json(path)
    assert any(stream["codec_type"] == stream_type for stream in metadata["streams"])


def test_list_endpoints_includes_public_routes(client):
    response = client.get("/endpoints")

    assert response.status_code == 200
    endpoints = response.json()["endpoints"]
    assert "/convert_to_mp3" in endpoints
    assert "/download/{file_id}" in endpoints


def test_convert_to_mp3_returns_file_id_and_downloadable_output(client, api_module, tmp_path):
    source = make_wav(tmp_path / "source.wav")

    response = upload(client, "/convert_to_mp3", source, "audio/wav")

    assert response.status_code == 200
    file_id = response.json()["file_id"]
    converted = output_path(api_module, file_id, "mp3")
    assert converted.exists()
    assert_has_stream(converted, "audio")
    assert_downloads(client, file_id)


def test_convert_to_wav_returns_wav_output(client, api_module, tmp_path):
    source = make_mp3(tmp_path / "source.mp3")

    response = upload(client, "/convert_to_wav", source, "audio/mpeg")

    assert response.status_code == 200
    converted = output_path(api_module, response.json()["file_id"], "wav")
    assert converted.exists()
    assert_has_stream(converted, "audio")


def test_convert_to_mp4_returns_video_output(client, api_module, tmp_path):
    source = make_avi(tmp_path / "source.avi")

    response = upload(client, "/convert_to_mp4", source, "video/x-msvideo")

    assert response.status_code == 200
    converted = output_path(api_module, response.json()["file_id"], "mp4")
    assert converted.exists()
    assert_has_stream(converted, "video")


def test_convert_image_to_jpg_returns_image_output(client, api_module, tmp_path):
    source = make_png(tmp_path / "source.png")

    response = upload(client, "/convert_image_to_jpg", source, "image/png")

    assert response.status_code == 200
    converted = output_path(api_module, response.json()["file_id"], "jpg")
    assert converted.exists()
    assert_has_stream(converted, "video")


def test_extract_audio_returns_wav_from_video(client, api_module, tmp_path):
    source = make_mp4(tmp_path / "source.mp4")

    response = upload(client, "/extract_audio", source, "video/mp4")

    assert response.status_code == 200
    extracted = output_path(api_module, response.json()["file_id"], "wav")
    assert extracted.exists()
    assert_has_stream(extracted, "audio")


def test_extract_images_returns_zip_with_jpg_frames(client, api_module, tmp_path):
    source = make_mp4(tmp_path / "source.mp4")

    response = upload(client, "/extract_images", source, "video/mp4")

    assert response.status_code == 200
    archive = output_path(api_module, response.json()["file_id"], "zip")
    assert archive.exists()
    with zipfile.ZipFile(archive) as zip_file:
        names = zip_file.namelist()
    assert names
    assert all(name.endswith(".jpg") for name in names)
    assert_downloads(client, response.json()["file_id"])


def test_probe_returns_ffprobe_json(client, tmp_path):
    source = make_mp4(tmp_path / "source.mp4")

    response = upload(client, "/probe", source, "video/mp4")

    assert response.status_code == 200
    metadata = response.json()
    assert "format" in metadata
    assert any(stream["codec_type"] == "video" for stream in metadata["streams"])


def test_extract_audio_to_mp3_returns_mp3_output(client, api_module, tmp_path):
    source = make_mp4(tmp_path / "source.mp4")

    response = upload(client, "/extract_audio_to_mp3", source, "video/mp4")

    assert response.status_code == 200
    extracted = output_path(api_module, response.json()["file_id"], "mp3")
    assert extracted.exists()
    assert_has_stream(extracted, "audio")


def test_split_mp3_returns_chunk_ids_and_downloadable_chunk(client, api_module, tmp_path):
    source = make_mp3(tmp_path / "source.mp3")

    response = upload(client, "/split_mp3", source, "audio/mpeg")

    assert response.status_code == 200
    chunk_ids = response.json()["chunk_file_ids"]
    assert len(chunk_ids) == 1
    chunk = Path(api_module.OUTPUT_DIR) / chunk_ids[0].split("_part")[0] / f"{chunk_ids[0]}.mp3"
    assert chunk.exists()
    assert_has_stream(chunk, "audio")
    assert_downloads(client, chunk_ids[0])


def test_scrubber_returns_named_scrubbed_output(client, api_module, tmp_path):
    source = make_mp3_with_leading_silence(tmp_path / "source.mp3")

    response = upload(client, "/scrubber", source, "audio/mpeg")

    assert response.status_code == 200
    body = response.json()
    assert body["output_file"] == f"{body['file_id']}_scrubbed.mp3"
    scrubbed = Path(api_module.OUTPUT_DIR) / body["output_file"]
    assert scrubbed.exists()
    assert_has_stream(scrubbed, "audio")
    assert_downloads(client, body["file_id"])


def test_download_missing_file_returns_404(client):
    response = client.get("/download/not-a-real-file")

    assert response.status_code == 404
    assert response.json()["detail"] == "File not found"
