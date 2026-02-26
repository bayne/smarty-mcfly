"""Shared pytest fixtures."""

import json
from pathlib import Path

import pytest


@pytest.fixture
def tmp_project(tmp_path: Path) -> Path:
    """A temporary directory serving as a project root."""
    return tmp_path


@pytest.fixture
def claude_settings(tmp_path: Path) -> Path:
    """A Claude Desktop-format settings.json file."""
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"mcpServers": {}}, indent=2) + "\n")
    return path


@pytest.fixture
def vscode_settings(tmp_path: Path) -> Path:
    """A VS Code MCP-format settings.json file."""
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"mcp": {"servers": {}}}, indent=2) + "\n")
    return path


@pytest.fixture
def smarts_dir(tmp_path: Path) -> Path:
    """A pre-created .smarts directory inside a temp project."""
    d = tmp_path / ".smarts"
    d.mkdir()
    return d
