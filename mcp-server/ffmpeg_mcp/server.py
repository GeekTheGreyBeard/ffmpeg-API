import os
from typing import Any

from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse

from .client import FfmpegApiClient


API_BASE_URL = os.getenv("FFMPEG_API_BASE_URL", "http://ffmpeg-api:8000")
MCP_HOST = os.getenv("FFMPEG_MCP_HOST", "0.0.0.0")
MCP_PORT = int(os.getenv("FFMPEG_MCP_PORT", "8080"))

mcp = FastMCP(
    "ffmpeg-api",
    instructions=(
        "Agent-facing MCP adapter for ffmpeg-API. Use base64 content for remote clients "
        "or file_path for trusted local/container-mounted files."
    ),
    host=MCP_HOST,
    port=MCP_PORT,
    streamable_http_path="/mcp",
    stateless_http=True,
    json_response=True,
)


def api_client() -> FfmpegApiClient:
    return FfmpegApiClient(API_BASE_URL)


@mcp.custom_route("/health", methods=["GET"])
async def http_health(request):
    return JSONResponse({"status": "ok", "service": "ffmpeg-mcp", "version": "1.2.0", "api_base_url": API_BASE_URL})


@mcp.tool()
async def health() -> dict[str, Any]:
    """Return ffmpeg-api health information."""
    return await api_client().health()


@mcp.tool()
async def list_endpoints() -> dict[str, Any]:
    """Return the ffmpeg-api endpoint catalog."""
    return await api_client().list_endpoints()


@mcp.tool()
async def convert_media(
    filename: str,
    format: str,
    content_base64: str | None = None,
    file_path: str | None = None,
    video_codec: str | None = None,
    audio_codec: str | None = None,
    video_bitrate: str | None = None,
    audio_bitrate: str | None = None,
    resolution: str | None = None,
    frame_rate: int | None = None,
    sample_rate: int | None = None,
    audio_channels: int | None = None,
    quality: str | None = None,
) -> dict[str, Any]:
    """Convert uploaded media using ffmpeg-api's generic conversion endpoint."""
    return await api_client().upload(
        "/convert",
        filename=filename,
        content_base64=content_base64,
        file_path=file_path,
        fields={
            "format": format,
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


@mcp.tool()
async def probe_media(filename: str, content_base64: str | None = None, file_path: str | None = None) -> dict[str, Any]:
    """Probe uploaded media and return FFprobe metadata."""
    return await api_client().upload("/probe", filename=filename, content_base64=content_base64, file_path=file_path)


@mcp.tool()
async def extract_audio(
    filename: str,
    output_format: str = "mp3",
    content_base64: str | None = None,
    file_path: str | None = None,
) -> dict[str, Any]:
    """Extract audio from uploaded media as mp3 or wav."""
    endpoint = "/extract_audio_to_mp3" if output_format.lower() == "mp3" else "/extract_audio"
    return await api_client().upload(endpoint, filename=filename, content_base64=content_base64, file_path=file_path)


@mcp.tool()
async def extract_frames(filename: str, content_base64: str | None = None, file_path: str | None = None) -> dict[str, Any]:
    """Extract frames from uploaded video into a ZIP artifact."""
    return await api_client().upload("/extract_images", filename=filename, content_base64=content_base64, file_path=file_path)


@mcp.tool()
async def split_mp3(filename: str, content_base64: str | None = None, file_path: str | None = None) -> dict[str, Any]:
    """Split an uploaded MP3 into approximately 23 MB chunks."""
    return await api_client().upload("/split_mp3", filename=filename, content_base64=content_base64, file_path=file_path)


@mcp.tool()
async def scrub_audio(filename: str, content_base64: str | None = None, file_path: str | None = None) -> dict[str, Any]:
    """Remove silence from uploaded audio using ffmpeg-api's scrubber endpoint."""
    return await api_client().upload("/scrubber", filename=filename, content_base64=content_base64, file_path=file_path)


@mcp.tool()
async def get_artifact(file_id: str) -> dict[str, Any]:
    """Return metadata for a generated artifact."""
    return await api_client().get_artifact(file_id)


@mcp.tool()
async def delete_artifact(file_id: str) -> dict[str, Any]:
    """Delete a generated artifact and its metadata."""
    return await api_client().delete_artifact(file_id)


def main() -> None:
    mcp.run(transport="streamable-http")


if __name__ == "__main__":
    main()

