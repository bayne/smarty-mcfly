"""Install MCP server configuration and agent rules into settings files."""

import copy
import difflib
import json
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.syntax import Syntax

console = Console()

MCP_SERVER_CONFIG: dict[str, Any] = {
    "command": "uvx",
    "args": ["smarty-mcfly", "serve"],
}

AGENT_RULE = """\

## Smarty McFly Documentation

When answering questions about software tools, libraries, or APIs:

1. Check `.smarts/MANIFEST.md` to see if relevant documentation exists for the topic.
2. If a matching topic is found in MANIFEST.md, read the markdown files in the \
referenced directory.
3. Use this documentation to provide accurate, up-to-date answers.
"""


def _display_diff_with_pager(original: str, modified: str, filename: str) -> bool:
    """Display a colored unified diff via the user's PAGER.

    Returns True if there are changes to apply, False if the content is identical.
    """
    original_lines = original.splitlines(keepends=True)
    modified_lines = modified.splitlines(keepends=True)

    diff = difflib.unified_diff(
        original_lines,
        modified_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
    )
    diff_text = "".join(diff)

    if not diff_text:
        console.print("[yellow]No changes needed.[/yellow]")
        return False

    syntax = Syntax(diff_text, "diff", theme="monokai")
    with console.pager(styles=True):
        console.print(syntax)

    return True


def _prompt_apply() -> bool:
    """Prompt the user to apply changes. Returns True if they confirm."""
    try:
        answer = input("Apply changes? [y/N] ").strip().lower()
        return answer == "y"
    except (KeyboardInterrupt, EOFError):
        print()
        return False


def _add_mcp_to_settings(settings: dict[str, Any]) -> dict[str, Any]:
    """Add smarty-mcfly MCP config to a settings dict.

    Handles both Claude Desktop format (mcpServers) and VS Code format (mcp.servers).
    """
    settings = copy.deepcopy(settings)

    if "mcp" in settings:
        # VS Code MCP settings format
        servers = settings["mcp"].setdefault("servers", {})
        servers["smarty-mcfly"] = {"type": "stdio", **MCP_SERVER_CONFIG}
    else:
        # Claude Desktop settings format
        servers = settings.setdefault("mcpServers", {})
        servers["smarty-mcfly"] = MCP_SERVER_CONFIG

    return settings


def install_mcp(settings_file: Path) -> None:
    """Install smarty-mcfly MCP server configuration into a settings.json file.

    Reads the file, generates a colored diff showing the changes, displays it
    via the user's PAGER, then prompts to apply.
    """
    settings_path = Path(settings_file)

    if not settings_path.exists():
        console.print(f"[red]Error: {settings_path} does not exist.[/red]")
        raise SystemExit(1)

    original_text = settings_path.read_text()
    try:
        settings = json.loads(original_text)
    except json.JSONDecodeError as e:
        console.print(f"[red]Error: Invalid JSON in {settings_path}: {e}[/red]")
        raise SystemExit(1)

    modified = _add_mcp_to_settings(settings)
    modified_text = json.dumps(modified, indent=2) + "\n"

    has_changes = _display_diff_with_pager(
        original_text, modified_text, settings_path.name
    )
    if not has_changes:
        return

    if _prompt_apply():
        settings_path.write_text(modified_text)
        console.print(f"[green]Changes applied to {settings_path}[/green]")
    else:
        console.print("[yellow]Changes not applied.[/yellow]")


def install_rules(rules_file: Path) -> None:
    """Install agent rules into a rules file.

    Appends a rule instructing the agent to check .smarts/MANIFEST.md for
    relevant documentation. Shows a colored diff via the user's PAGER and
    prompts to apply.
    """
    rules_path = Path(rules_file)

    original_text = rules_path.read_text() if rules_path.exists() else ""

    if ".smarts" in original_text or "Smarty McFly" in original_text:
        console.print("[yellow]Smarty McFly rules already present in file.[/yellow]")
        return

    separator = "" if original_text.endswith("\n") or not original_text else "\n"
    modified_text = original_text + separator + AGENT_RULE

    has_changes = _display_diff_with_pager(
        original_text, modified_text, rules_path.name
    )
    if not has_changes:
        return

    if _prompt_apply():
        rules_path.parent.mkdir(parents=True, exist_ok=True)
        rules_path.write_text(modified_text)
        console.print(f"[green]Changes applied to {rules_path}[/green]")
    else:
        console.print("[yellow]Changes not applied.[/yellow]")
