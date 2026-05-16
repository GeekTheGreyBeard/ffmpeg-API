import base64

import pytest

from ffmpeg_mcp.client import FfmpegApiClient


def test_client_rejects_missing_upload_source():
    client = FfmpegApiClient("http://example.test")

    with pytest.raises(ValueError, match="Provide either"):
        client._load_content(None, None)


def test_client_rejects_two_upload_sources(tmp_path):
    source = tmp_path / "source.txt"
    source.write_text("hello", encoding="utf-8")
    client = FfmpegApiClient("http://example.test")

    with pytest.raises(ValueError, match="Provide only one"):
        # Exercise the public validation path without making an HTTP request.
        import asyncio

        asyncio.run(client.upload("/convert", filename="source.txt", content_base64="aGVsbG8=", file_path=str(source)))


def test_client_loads_base64_content():
    client = FfmpegApiClient("http://example.test")
    payload = base64.b64encode(b"media").decode()

    assert client._load_content(payload, None) == b"media"


def test_client_clean_fields_omits_none_and_stringifies_values():
    client = FfmpegApiClient("http://example.test")

    assert client._clean_fields({"format": "mp3", "sample_rate": 44100, "quality": None}) == {
        "format": "mp3",
        "sample_rate": "44100",
    }
