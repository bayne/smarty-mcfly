# smarty-mcfly

A CLI tool and MCP server for generating and reading markdown documentation of software tools, libraries, and APIs. Documentation is stored locally in a `.smarts/` directory and accessible to AI agents via the Model Context Protocol (MCP).

## Overview

smarty-mcfly lets you fetch documentation from a variety of sources (web pages, man pages, JavaDoc, Sphinx/ReadTheDocs, Go docs, Rust docs), convert it to GitHub Flavored Markdown, and store it in a local `.smarts/` directory. An MCP server exposes all of this to AI assistants like Claude.

## Installation

Requires Python >=3.12 and [uv](https://docs.astral.sh/uv/).

```bash
# Install and run directly with uvx (no install needed)
uvx smarty-mcfly --help

# Or install into a project
uv add smarty-mcfly
```

## Quick Start

```bash
# 1. Initialize your project's .smarts/ directory with pre-built docs
smarty-mcfly smarts

# 2. Install the MCP server into Claude Desktop
smarty-mcfly install mcp ~/Library/Application\ Support/Claude/claude_desktop_config.json

# 3. Add the agent rule to your CLAUDE.md
smarty-mcfly install rules CLAUDE.md

# 4. Learn new documentation
smarty-mcfly learn python requests --url https://requests.readthedocs.io/en/latest/
```

## Commands

### `smarts`

Clone the pre-built `.smarts/` documentation directory from the smarty-mcfly repository into your project.

```bash
smarty-mcfly smarts [--project-root PATH]
```

If `.smarts/` already exists, this is a no-op.

### `serve`

Start the MCP server over stdio. This is what AI clients connect to.

```bash
smarty-mcfly serve
```

The MCP entry point for settings files:
```json
{
  "command": "uvx",
  "args": ["smarty-mcfly", "serve"]
}
```

### `install mcp <file>`

Add the smarty-mcfly MCP server entry to a Claude Desktop or VS Code settings file. Shows a colored diff and prompts for confirmation before writing.

```bash
# Claude Desktop
smarty-mcfly install mcp ~/Library/Application\ Support/Claude/claude_desktop_config.json

# VS Code
smarty-mcfly install mcp ~/.config/Code/User/settings.json
```

### `install rules <file>`

Append the smarty-mcfly agent rule to a rules file (e.g. `CLAUDE.md`, `.cursorrules`). Skips if a rule already exists.

```bash
smarty-mcfly install rules CLAUDE.md
smarty-mcfly install rules .cursorrules
```

### `learn <topic> <subtopic> --<source>`

Fetch documentation and save it as markdown to `.smarts/<topic>/<subtopic>.md`. Exactly one source flag is required.

```bash
# From a URL (HTML converted to GFM markdown via pandoc)
smarty-mcfly learn python requests --url https://docs.python-requests.org/

# From a man page
smarty-mcfly learn git rebase --man git-rebase

# From JavaDoc (full URL or Maven coordinates group:artifact:version)
smarty-mcfly learn java gson --javadoc com.google.code.gson:gson:2.10.1

# From Sphinx/ReadTheDocs (full URL or package name)
smarty-mcfly learn python boto3 --sphinx boto3

# From Go docs (module path, uses `go doc` if available, falls back to pkg.go.dev)
smarty-mcfly learn go chi --godoc github.com/go-chi/chi/v5

# From Rust docs (crate name or full URL)
smarty-mcfly learn rust serde --rustdoc serde
```

All learned documentation is indexed in `.smarts/MANIFEST.md`.

## MCP Tools

When running as an MCP server (`smarty-mcfly serve`), the following tools are available:

| Tool | Description |
|------|-------------|
| `setup_smarts` | Clone the pre-built .smarts directory |
| `learn_from_url` | Fetch and convert a web page |
| `learn_from_man` | Convert a man page |
| `learn_from_javadoc` | Fetch JavaDoc (URL or Maven coords) |
| `learn_from_sphinx` | Fetch Sphinx/ReadTheDocs docs |
| `learn_from_godoc` | Fetch Go package docs |
| `learn_from_rustdoc` | Fetch Rust crate docs |

All tools accept a `project_root` parameter (defaults to current working directory).

## Project Structure

Documentation is stored under `.smarts/` in your project:

```
.smarts/
├── MANIFEST.md          # Index of all learned documentation
├── python/
│   ├── requests.md
│   └── boto3.md
├── rust/
│   └── serde.md
└── ...
```

## Development

```bash
# Install dev dependencies
uv sync --group dev

# Run tests (excluding network)
uv run pytest tests/ -m "not network"

# Run network tests
uv run pytest tests/ -m network

# Run CLI locally
uv run smarty-mcfly --help
```
