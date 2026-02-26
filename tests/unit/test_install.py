"""Unit tests for smarty_mcfly.commands.install."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from smarty_mcfly.commands.install import (
    AGENT_RULE,
    MCP_SERVER_CONFIG,
    _add_mcp_to_settings,
    _display_diff_with_pager,
    _prompt_apply,
    install_mcp,
    install_rules,
)


class TestAddMcpToSettings:
    def test_claude_desktop_format_adds_to_mcp_servers(self):
        result = _add_mcp_to_settings({})
        assert "mcpServers" in result
        assert "smarty-mcfly" in result["mcpServers"]
        assert result["mcpServers"]["smarty-mcfly"] == MCP_SERVER_CONFIG

    def test_vscode_format_adds_with_type_stdio(self):
        result = _add_mcp_to_settings({"mcp": {"servers": {}}})
        entry = result["mcp"]["servers"]["smarty-mcfly"]
        assert entry["type"] == "stdio"
        assert entry["command"] == MCP_SERVER_CONFIG["command"]
        assert entry["args"] == MCP_SERVER_CONFIG["args"]

    def test_claude_format_creates_mcp_servers_key_if_missing(self):
        result = _add_mcp_to_settings({"theme": "dark"})
        assert "mcpServers" in result
        assert "theme" in result  # other keys preserved

    def test_preserves_existing_mcp_servers(self):
        settings = {"mcpServers": {"other-server": {"command": "foo"}}}
        result = _add_mcp_to_settings(settings)
        assert "other-server" in result["mcpServers"]
        assert "smarty-mcfly" in result["mcpServers"]

    def test_vscode_creates_servers_key_if_missing(self):
        result = _add_mcp_to_settings({"mcp": {}})
        assert "servers" in result["mcp"]
        assert "smarty-mcfly" in result["mcp"]["servers"]

    def test_does_not_mutate_input(self):
        settings = {"mcpServers": {}}
        _add_mcp_to_settings(settings)
        assert "smarty-mcfly" not in settings["mcpServers"]


class TestDisplayDiffWithPager:
    def test_returns_false_when_content_identical(self):
        with patch("smarty_mcfly.commands.install.console"):
            result = _display_diff_with_pager("same\n", "same\n", "file.json")
        assert result is False

    def test_returns_true_when_content_differs(self):
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=None)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        with patch("smarty_mcfly.commands.install.console") as mock_console:
            mock_console.pager.return_value = mock_ctx
            result = _display_diff_with_pager("old\n", "new\n", "file.json")
        assert result is True

    def test_calls_pager_with_styles(self):
        mock_ctx = MagicMock()
        mock_ctx.__enter__ = MagicMock(return_value=None)
        mock_ctx.__exit__ = MagicMock(return_value=False)
        with patch("smarty_mcfly.commands.install.console") as mock_console:
            mock_console.pager.return_value = mock_ctx
            _display_diff_with_pager("a\n", "b\n", "file.json")
        mock_console.pager.assert_called_once_with(styles=True)


class TestPromptApply:
    def test_returns_true_on_y(self):
        with patch("builtins.input", return_value="y"):
            assert _prompt_apply() is True

    def test_returns_true_on_uppercase_y(self):
        with patch("builtins.input", return_value="Y"):
            assert _prompt_apply() is True

    def test_returns_false_on_n(self):
        with patch("builtins.input", return_value="n"):
            assert _prompt_apply() is False

    def test_returns_false_on_empty_input(self):
        with patch("builtins.input", return_value=""):
            assert _prompt_apply() is False

    def test_returns_false_on_keyboard_interrupt(self):
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            assert _prompt_apply() is False

    def test_returns_false_on_eof(self):
        with patch("builtins.input", side_effect=EOFError):
            assert _prompt_apply() is False


class TestInstallMcp:
    def test_exits_when_file_does_not_exist(self, tmp_path):
        with pytest.raises(SystemExit):
            install_mcp(tmp_path / "missing.json")

    def test_exits_on_invalid_json(self, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("{ not valid json }")
        with pytest.raises(SystemExit):
            install_mcp(bad)

    def test_writes_changes_when_user_confirms(self, claude_settings):
        with (
            patch(
                "smarty_mcfly.commands.install._display_diff_with_pager",
                return_value=True,
            ),
            patch("smarty_mcfly.commands.install._prompt_apply", return_value=True),
        ):
            install_mcp(claude_settings)

        result = json.loads(claude_settings.read_text())
        assert "smarty-mcfly" in result["mcpServers"]

    def test_does_not_write_when_user_rejects(self, claude_settings):
        original = claude_settings.read_text()
        with (
            patch(
                "smarty_mcfly.commands.install._display_diff_with_pager",
                return_value=True,
            ),
            patch("smarty_mcfly.commands.install._prompt_apply", return_value=False),
        ):
            install_mcp(claude_settings)

        assert claude_settings.read_text() == original

    def test_skips_prompt_when_no_diff(self, tmp_path):
        # File already has smarty-mcfly configured — diff will be empty
        existing = {"mcpServers": {"smarty-mcfly": MCP_SERVER_CONFIG}}
        f = tmp_path / "settings.json"
        f.write_text(json.dumps(existing, indent=2) + "\n")

        with (
            patch(
                "smarty_mcfly.commands.install._display_diff_with_pager",
                return_value=False,
            ) as mock_diff,
            patch("smarty_mcfly.commands.install._prompt_apply") as mock_prompt,
        ):
            install_mcp(f)

        mock_prompt.assert_not_called()

    def test_handles_vscode_settings_format(self, vscode_settings):
        with (
            patch(
                "smarty_mcfly.commands.install._display_diff_with_pager",
                return_value=True,
            ),
            patch("smarty_mcfly.commands.install._prompt_apply", return_value=True),
        ):
            install_mcp(vscode_settings)

        result = json.loads(vscode_settings.read_text())
        assert "smarty-mcfly" in result["mcp"]["servers"]


class TestInstallRules:
    def test_skips_if_smarts_already_in_file(self, tmp_path):
        rules_file = tmp_path / "CLAUDE.md"
        rules_file.write_text("Check .smarts/MANIFEST.md for docs\n")

        with patch(
            "smarty_mcfly.commands.install._display_diff_with_pager"
        ) as mock_diff:
            install_rules(rules_file)

        mock_diff.assert_not_called()

    def test_skips_if_smarty_mcfly_heading_present(self, tmp_path):
        rules_file = tmp_path / "CLAUDE.md"
        rules_file.write_text("## Smarty McFly Documentation\n")

        with patch(
            "smarty_mcfly.commands.install._display_diff_with_pager"
        ) as mock_diff:
            install_rules(rules_file)

        mock_diff.assert_not_called()

    def test_creates_new_file_when_missing(self, tmp_path):
        rules_file = tmp_path / "CLAUDE.md"
        with (
            patch(
                "smarty_mcfly.commands.install._display_diff_with_pager",
                return_value=True,
            ),
            patch("smarty_mcfly.commands.install._prompt_apply", return_value=True),
        ):
            install_rules(rules_file)

        content = rules_file.read_text()
        assert ".smarts" in content
        assert "MANIFEST.md" in content

    def test_appends_to_existing_file(self, tmp_path):
        rules_file = tmp_path / "CLAUDE.md"
        rules_file.write_text("# Existing Rules\n\nDo something.\n")

        with (
            patch(
                "smarty_mcfly.commands.install._display_diff_with_pager",
                return_value=True,
            ),
            patch("smarty_mcfly.commands.install._prompt_apply", return_value=True),
        ):
            install_rules(rules_file)

        content = rules_file.read_text()
        assert "# Existing Rules" in content
        assert ".smarts" in content

    def test_does_not_write_when_user_rejects(self, tmp_path):
        rules_file = tmp_path / "CLAUDE.md"
        original = "# Original\n"
        rules_file.write_text(original)

        with (
            patch(
                "smarty_mcfly.commands.install._display_diff_with_pager",
                return_value=True,
            ),
            patch("smarty_mcfly.commands.install._prompt_apply", return_value=False),
        ):
            install_rules(rules_file)

        assert rules_file.read_text() == original

    def test_creates_parent_directories(self, tmp_path):
        rules_file = tmp_path / "nested" / "dir" / "CLAUDE.md"

        with (
            patch(
                "smarty_mcfly.commands.install._display_diff_with_pager",
                return_value=True,
            ),
            patch("smarty_mcfly.commands.install._prompt_apply", return_value=True),
        ):
            install_rules(rules_file)

        assert rules_file.exists()
