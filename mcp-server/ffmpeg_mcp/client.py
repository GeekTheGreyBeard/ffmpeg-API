import base64
import mimetypes
from pathlib import Path
from typing import Any

import httpx


class FfmpegApiClient:
    def __init__(self, base_url: str, timeout: float = 120.0):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    async def health(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()

    async def list_endpoints(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/endpoints")
            response.raise_for_status()
            return response.json()

    async def get_artifact(self, file_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/artifacts/{file_id}")
            response.raise_for_status()
            return response.json()

    async def delete_artifact(self, file_id: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.delete(f"{self.base_url}/artifacts/{file_id}")
            response.raise_for_status()
            return response.json()

    async def upload(
        self,
        endpoint: str,
        *,
        filename: str,
        content_base64: str | None = None,
        file_path: str | None = None,
        fields: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if not content_base64 and not file_path:
            raise ValueError("Provide either content_base64 or file_path")
        if content_base64 and file_path:
            raise ValueError("Provide only one of content_base64 or file_path")

        content = self._load_content(content_base64, file_path)
        mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        files = {"file": (filename, content, mime_type)}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.base_url}/{endpoint.lstrip('/')}",
                data=self._clean_fields(fields or {}),
                files=files,
            )
            response.raise_for_status()
            return response.json()

    def _load_content(self, content_base64: str | None, file_path: str | None) -> bytes:
        if content_base64:
            return base64.b64decode(content_base64)
        if not file_path:
            raise ValueError("Provide either content_base64 or file_path")
        path = Path(file_path or "")
        if not path.exists() or not path.is_file():
            raise ValueError(f"File does not exist: {path}")
        return path.read_bytes()

    def _clean_fields(self, fields: dict[str, Any]) -> dict[str, str]:
        return {key: str(value) for key, value in fields.items() if value is not None}
