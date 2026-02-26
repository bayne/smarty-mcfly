# CLAUDE.md

## Smarty McFly Documentation

When answering questions about software tools, libraries, or APIs:

1. Check `.smarts/MANIFEST.md` to see if relevant documentation exists for the topic.
2. If a matching topic is found in MANIFEST.md, read the markdown files in the referenced directory.
3. Use this documentation to provide accurate, up-to-date answers.

---

## Project: smarty-mcfly

### Overview

CLI tool and MCP server that fetches documentation from various sources, converts it to GitHub Flavored Markdown via pandoc, and stores it in `.smarts/`. The same commands are available both as CLI subcommands and as MCP tools.

### Running the Project

```bash
uv run smarty-mcfly --help       # CLI
uv run pytest tests/ -m "not network"  # Tests (no network)
uv run pytest tests/ -m network        # Network-dependent tests
uv sync --group dev                    # Install dev deps
```

### Package Structure

```
smarty_mcfly/
├── cli.py          # cyclopts CLI entry point
├── server.py       # FastMCP server (all MCP tools)
└── commands/
    ├── smarts.py   # Clone .smarts from git repo
    ├── install.py  # install mcp / install rules
    └── learn.py    # learn from --url/--man/--javadoc/--sphinx/--godoc/--rustdoc
```

### Key Conventions

- **CLI binary:** `smarty-mcfly` (defined in `pyproject.toml` scripts)
- **MCP server:** `smarty-mcfly serve` (stdio transport)
- **MCP config entry:** `{"command": "uvx", "args": ["smarty-mcfly", "serve"]}`
- **Package manager:** `uv` — use `uv add <pkg>` to add deps, `uv run` to execute
- **Python version:** >=3.12

### Testing Conventions

- Unit tests in `tests/unit/` — mock subprocess, httpx, and filesystem
- E2E tests in `tests/e2e/` — invoke CLI via `subprocess.run(["uv", "run", "smarty-mcfly", ...])`
- E2E tests set `NO_COLOR=1 PAGER=cat` in the subprocess environment
- Network tests are marked `@pytest.mark.network` and excluded by default
- Fixtures: `tmp_project`, `claude_settings`, `vscode_settings`, `smarts_dir` in `conftest.py`
- FastMCP tool enumeration: `asyncio.run(mcp.list_tools())` returns tool objects with `.name`

### Architecture Notes

- `learn.py` pipeline: fetch → pandoc (HTML/man/text → GFM) → save to `.smarts/<topic>/<subtopic>.md` → update `MANIFEST.md`
- `install.py` shows a colored unified diff via Rich pager before writing any file
- `smarts.py` shallow-clones the repo (`--depth=1`) and copies `smarts/` → `.smarts/`
- Settings detection: Claude Desktop uses `mcpServers` key; VS Code uses `mcp.servers`
- `learn_godoc` tries `go doc -all <module>` first, falls back to `https://pkg.go.dev/<module>`
- Maven coordinates format: `group:artifact:version` → `https://javadoc.io/doc/group/artifact/version`
