"""CLI interface for smarty-mcfly."""

from pathlib import Path
from typing import Optional

import cyclopts

from .commands import install as install_cmd
from .commands import learn as learn_cmd
from .commands import smarts as smarts_cmd

app = cyclopts.App(
    name="smarty-mcfly",
    help="CLI tool and MCP server for managing software documentation as markdown.",
)

install_app = cyclopts.App(
    name="install",
    help="Install MCP server configuration or agent rules into settings files.",
)
app.command(install_app)


@app.command
def smarts(project_root: Path = Path(".")) -> None:
    """Clone the .smarts documentation directory into the project if it doesn't exist."""
    result = smarts_cmd.ensure_smarts(str(project_root))
    print(result)


@app.command
def serve() -> None:
    """Start the smarty-mcfly MCP server (for use with Claude Desktop, VS Code, etc.)."""
    from .server import mcp

    mcp.run(transport="stdio")


@install_app.command
def mcp(settings_file: Path) -> None:
    """Install the smarty-mcfly MCP server into a settings.json file.

    Supports both Claude Desktop and VS Code MCP settings formats.
    Displays a colored diff via your PAGER and prompts before applying.
    """
    install_cmd.install_mcp(settings_file)


@install_app.command
def rules(rules_file: Path) -> None:
    """Install agent rules into a rules file (e.g. CLAUDE.md, .cursorrules).

    Appends a rule that instructs the agent to consult .smarts/MANIFEST.md
    for relevant documentation topics. Displays a diff and prompts before applying.
    """
    install_cmd.install_rules(rules_file)


@app.command
def learn(
    topic: str,
    subtopic: str,
    *,
    url: Optional[str] = None,
    man: Optional[str] = None,
    javadoc: Optional[str] = None,
    sphinx: Optional[str] = None,
    godoc: Optional[str] = None,
    rustdoc: Optional[str] = None,
    project_root: Path = Path("."),
) -> None:
    """Fetch documentation from a source, convert to markdown, and store in .smarts/.

    Exactly one source flag must be provided:

    \b
      --url URL        Fetch a web page and convert via pandoc
      --man PAGE       Convert a man page via pandoc
      --javadoc ID     Fetch JavaDoc (URL or Maven coordinate group:artifact:version)
      --sphinx PKG     Fetch Sphinx docs (URL or ReadTheDocs package name)
      --godoc MOD      Fetch Go docs (URL or module path via go doc / pkg.go.dev)
      --rustdoc CRATE  Fetch Rust docs (URL or crate name via docs.rs)
    """
    root = str(project_root)
    sources = {
        "url": url,
        "man": man,
        "javadoc": javadoc,
        "sphinx": sphinx,
        "godoc": godoc,
        "rustdoc": rustdoc,
    }
    provided = {k: v for k, v in sources.items() if v is not None}

    if not provided:
        print(
            "Error: specify one of --url, --man, --javadoc, --sphinx, --godoc, --rustdoc"
        )
        raise SystemExit(1)
    if len(provided) > 1:
        print(f"Error: only one source flag allowed, got: {', '.join(provided)}")
        raise SystemExit(1)

    source, value = next(iter(provided.items()))
    dispatch = {
        "url": learn_cmd.learn_url,
        "man": learn_cmd.learn_man,
        "javadoc": learn_cmd.learn_javadoc,
        "sphinx": learn_cmd.learn_sphinx,
        "godoc": learn_cmd.learn_godoc,
        "rustdoc": learn_cmd.learn_rustdoc,
    }
    result = dispatch[source](topic, subtopic, value, root)
    print(result)


def main() -> None:
    app()
