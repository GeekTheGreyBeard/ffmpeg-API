import importlib
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def api_module(tmp_path, monkeypatch):
    project_root = Path(__file__).resolve().parents[1]
    monkeypatch.syspath_prepend(str(project_root))
    monkeypatch.chdir(tmp_path)

    sys.modules.pop("ffmpeg_api", None)
    module = importlib.import_module("ffmpeg_api")

    module.UPLOAD_DIR = str(tmp_path / "uploads")
    module.OUTPUT_DIR = str(tmp_path / "outputs")
    Path(module.UPLOAD_DIR).mkdir(exist_ok=True)
    Path(module.OUTPUT_DIR).mkdir(exist_ok=True)

    return module


@pytest.fixture
def client(api_module):
    with TestClient(api_module.app) as test_client:
        yield test_client
