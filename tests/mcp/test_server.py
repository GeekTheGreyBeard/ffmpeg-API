import base64

import pytest

from ffmpeg_mcp import server


class FakeClient:
    async def health(self):
        return {"status": "ok", "version": "1.2.0"}

    async def list_endpoints(self):
        return {"endpoints": {"/convert": "Convert media"}}

    async def get_artifact(self, file_id):
        return {"file_id": file_id}

    async def delete_artifact(self, file_id):
        return {"deleted": True, "file_id": file_id}

    async def upload(self, endpoint, *, filename, content_base64=None, file_path=None, fields=None):
        return {
            "endpoint": endpoint,
            "filename": filename,
            "content_base64": content_base64,
            "file_path": file_path,
            "fields": fields or {},
        }


@pytest.fixture(autouse=True)
def fake_client(monkeypatch):
    monkeypatch.setattr(server, "api_client", lambda: FakeClient())


@pytest.mark.asyncio
async def test_mcp_registers_expected_tools():
    tools = await server.mcp.list_tools()
    names = {tool.name for tool in tools}

    assert {
        "health",
        "list_endpoints",
        "convert_media",
        "probe_media",
        "extract_audio",
        "extract_frames",
        "split_mp3",
        "scrub_audio",
        "get_artifact",
        "delete_artifact",
    }.issubset(names)


@pytest.mark.asyncio
async def test_convert_media_maps_to_api_convert():
    payload = base64.b64encode(b"media").decode()

    result = await server.convert_media(
        filename="sample.wav",
        format="mp3",
        content_base64=payload,
        audio_codec="libmp3lame",
        audio_bitrate="96k",
    )

    assert result["endpoint"] == "/convert"
    assert result["filename"] == "sample.wav"
    assert result["content_base64"] == payload
    assert result["fields"]["format"] == "mp3"
    assert result["fields"]["audio_codec"] == "libmp3lame"
    assert result["fields"]["audio_bitrate"] == "96k"


@pytest.mark.asyncio
async def test_extract_audio_defaults_to_mp3_endpoint():
    result = await server.extract_audio(filename="sample.mp4", content_base64="bWVkaWE=")

    assert result["endpoint"] == "/extract_audio_to_mp3"


@pytest.mark.asyncio
async def test_artifact_tools_delegate_to_api_client():
    assert await server.get_artifact("abc") == {"file_id": "abc"}
    assert await server.delete_artifact("abc") == {"deleted": True, "file_id": "abc"}
