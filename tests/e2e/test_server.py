"""End-to-end tests for the MCP server module."""

import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent


class TestMcpServerTools:
    """Verify the MCP server is loadable and has the expected tools registered."""

    def test_server_imports_without_error(self):
        result = subprocess.run(
            ["uv", "run", "python", "-c", "from smarty_mcfly.server import mcp"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0, result.stderr

    def test_server_has_correct_name(self):
        result = subprocess.run(
            [
                "uv",
                "run",
                "python",
                "-c",
                "from smarty_mcfly.server import mcp; print(mcp.name)",
            ],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0
        assert "smarty-mcfly" in result.stdout

    def test_all_expected_tools_registered(self):
        """All MCP tools should be discoverable on the FastMCP app."""
        expected_tools = [
            "setup_smarts",
            "learn_from_url",
            "learn_from_man",
            "learn_from_javadoc",
            "learn_from_sphinx",
            "learn_from_godoc",
            "learn_from_rustdoc",
        ]
        script = (
            "from smarty_mcfly.server import mcp; "
            "import asyncio; "
            "tools = asyncio.run(mcp.list_tools()); "
            "print('\\n'.join(t.name for t in tools))"
        )
        result = subprocess.run(
            ["uv", "run", "python", "-c", script],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
        )
        assert result.returncode == 0, result.stderr
        registered = result.stdout
        for tool in expected_tools:
            assert tool in registered, f"Tool '{tool}' not registered in MCP server"


class TestServeCommand:
    def test_serve_is_available_as_cli_command(self):
        """The 'serve' subcommand should appear in --help output."""
        result = subprocess.run(
            ["uv", "run", "smarty-mcfly", "--help"],
            capture_output=True,
            text=True,
            cwd=str(PROJECT_ROOT),
            env={"NO_COLOR": "1", "TERM": "dumb", **__import__("os").environ},
        )
        assert result.returncode == 0
        assert "serve" in result.stdout
