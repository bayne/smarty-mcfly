"""End-to-end tests for the smarty-mcfly CLI.

These tests invoke the CLI via subprocess and verify exit codes, stdout, and
filesystem effects. Network-dependent tests are marked with @pytest.mark.network
and are skipped by default (run with: pytest -m network).
"""

import json
import os
import subprocess
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent


def run_cli(*args, stdin: str = "", env: dict | None = None) -> subprocess.CompletedProcess:
    """Run the CLI under uv and return the result."""
    test_env = {
        **os.environ,
        "NO_COLOR": "1",
        "TERM": "dumb",
        "PAGER": "cat",
    }
    if env:
        test_env.update(env)

    return subprocess.run(
        ["uv", "run", "smarty-mcfly", *args],
        capture_output=True,
        text=True,
        cwd=str(PROJECT_ROOT),
        input=stdin,
        env=test_env,
    )


# ---------------------------------------------------------------------------
# Help output
# ---------------------------------------------------------------------------


class TestHelpOutput:
    def test_root_help_exits_zero(self):
        result = run_cli("--help")
        assert result.returncode == 0

    def test_root_help_lists_all_commands(self):
        result = run_cli("--help")
        output = result.stdout
        assert "learn" in output
        assert "install" in output
        assert "smarts" in output
        assert "serve" in output

    def test_install_help_lists_subcommands(self):
        result = run_cli("install", "--help")
        assert result.returncode == 0
        assert "mcp" in result.stdout
        assert "rules" in result.stdout

    def test_learn_help_lists_all_source_flags(self):
        result = run_cli("learn", "--help")
        assert result.returncode == 0
        for flag in ("--url", "--man", "--javadoc", "--sphinx", "--godoc", "--rustdoc"):
            assert flag in result.stdout

    def test_smarts_help_exits_zero(self):
        result = run_cli("smarts", "--help")
        assert result.returncode == 0


# ---------------------------------------------------------------------------
# learn argument validation
# ---------------------------------------------------------------------------


class TestLearnValidation:
    def test_fails_when_no_source_flag(self, tmp_path):
        result = run_cli(
            "learn", "python", "requests", "--project-root", str(tmp_path)
        )
        assert result.returncode != 0
        combined = result.stdout + result.stderr
        assert "Error" in combined

    def test_fails_when_multiple_source_flags(self, tmp_path):
        result = run_cli(
            "learn",
            "python",
            "requests",
            "--url",
            "https://example.com",
            "--man",
            "ls",
            "--project-root",
            str(tmp_path),
        )
        assert result.returncode != 0

    def test_fails_when_topic_missing(self):
        result = run_cli("learn")
        assert result.returncode != 0

    def test_fails_when_subtopic_missing(self):
        result = run_cli("learn", "python")
        assert result.returncode != 0


# ---------------------------------------------------------------------------
# install mcp
# ---------------------------------------------------------------------------


class TestInstallMcp:
    def test_fails_on_missing_settings_file(self, tmp_path):
        result = run_cli("install", "mcp", str(tmp_path / "nonexistent.json"))
        assert result.returncode != 0

    def test_applies_claude_format_on_yes(self, tmp_path):
        settings = tmp_path / "settings.json"
        settings.write_text(json.dumps({"mcpServers": {}}, indent=2) + "\n")

        result = run_cli("install", "mcp", str(settings), stdin="y\n")

        assert result.returncode == 0
        updated = json.loads(settings.read_text())
        assert "smarty-mcfly" in updated["mcpServers"]

    def test_does_not_write_on_no(self, tmp_path):
        original_data = {"mcpServers": {}}
        settings = tmp_path / "settings.json"
        settings.write_text(json.dumps(original_data, indent=2) + "\n")

        result = run_cli("install", "mcp", str(settings), stdin="n\n")

        assert result.returncode == 0
        assert json.loads(settings.read_text()) == original_data

    def test_applies_vscode_format_on_yes(self, tmp_path):
        settings = tmp_path / "settings.json"
        settings.write_text(json.dumps({"mcp": {"servers": {}}}, indent=2) + "\n")

        result = run_cli("install", "mcp", str(settings), stdin="y\n")

        assert result.returncode == 0
        updated = json.loads(settings.read_text())
        entry = updated["mcp"]["servers"]["smarty-mcfly"]
        assert entry["type"] == "stdio"
        assert "smarty-mcfly" in entry["args"]

    def test_reports_no_changes_if_already_configured(self, tmp_path):
        existing = {
            "mcpServers": {
                "smarty-mcfly": {"command": "uvx", "args": ["smarty-mcfly", "serve"]}
            }
        }
        settings = tmp_path / "settings.json"
        settings.write_text(json.dumps(existing, indent=2) + "\n")

        result = run_cli("install", "mcp", str(settings))

        assert result.returncode == 0
        assert "No changes" in result.stdout


# ---------------------------------------------------------------------------
# install rules
# ---------------------------------------------------------------------------


class TestInstallRules:
    def test_creates_new_rules_file_on_yes(self, tmp_path):
        rules = tmp_path / "CLAUDE.md"

        result = run_cli("install", "rules", str(rules), stdin="y\n")

        assert result.returncode == 0
        content = rules.read_text()
        assert ".smarts" in content
        assert "MANIFEST.md" in content

    def test_appends_to_existing_file_on_yes(self, tmp_path):
        rules = tmp_path / "CLAUDE.md"
        rules.write_text("# My Rules\n\nDo stuff.\n")

        result = run_cli("install", "rules", str(rules), stdin="y\n")

        assert result.returncode == 0
        content = rules.read_text()
        assert "# My Rules" in content
        assert ".smarts" in content

    def test_does_not_write_on_no(self, tmp_path):
        rules = tmp_path / "CLAUDE.md"
        original = "# Original\n"
        rules.write_text(original)

        result = run_cli("install", "rules", str(rules), stdin="n\n")

        assert result.returncode == 0
        assert rules.read_text() == original

    def test_skips_when_rules_already_present(self, tmp_path):
        rules = tmp_path / "CLAUDE.md"
        existing = "Check .smarts/MANIFEST.md for documentation.\n"
        rules.write_text(existing)

        result = run_cli("install", "rules", str(rules))

        assert result.returncode == 0
        assert rules.read_text() == existing
        assert "already present" in result.stdout


# ---------------------------------------------------------------------------
# smarts (network-free: tests early-exit when .smarts exists)
# ---------------------------------------------------------------------------


class TestSmartsCommand:
    def test_reports_already_available_when_smarts_exists(self, tmp_path):
        (tmp_path / ".smarts").mkdir()

        result = run_cli("smarts", str(tmp_path))

        assert result.returncode == 0
        assert "already available" in result.stdout


# ---------------------------------------------------------------------------
# learn integration (network required)
# ---------------------------------------------------------------------------


class TestLearnIntegration:
    @pytest.mark.network
    def test_learn_from_url(self, tmp_path):
        result = run_cli(
            "learn",
            "example",
            "httpbin",
            "--url",
            "https://httpbin.org/html",
            "--project-root",
            str(tmp_path),
        )
        assert result.returncode == 0
        doc = tmp_path / ".smarts" / "example" / "httpbin.md"
        assert doc.exists()
        assert len(doc.read_text()) > 0

    @pytest.mark.network
    def test_learn_updates_manifest(self, tmp_path):
        run_cli(
            "learn",
            "example",
            "page",
            "--url",
            "https://httpbin.org/html",
            "--project-root",
            str(tmp_path),
        )
        manifest = tmp_path / ".smarts" / "MANIFEST.md"
        assert manifest.exists()
        content = manifest.read_text()
        assert "## example" in content
        assert "page" in content
