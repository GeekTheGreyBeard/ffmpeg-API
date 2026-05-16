import sys
from pathlib import Path


MCP_ROOT = Path(__file__).resolve().parents[2] / "mcp-server"
sys.path.insert(0, str(MCP_ROOT))
