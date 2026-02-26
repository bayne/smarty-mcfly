from mcp.server.fastmcp import FastMCP
import os

DOCS_SOURCE = os.path.expanduser("./smarts")

mcp = FastMCP("smarty-mcfly")

@mcp.tool()
def smarty_mcfly_symlink(project_root: str) -> str:
    """Create a symlink to shared docs in the project if it doesn't exist."""
    link_path = os.path.join(project_root, ".agent-docs")
    if os.path.islink(link_path) or os.path.exists(link_path):
        return f"Docs already available at {link_path}"
    os.makedirs(os.path.dirname(link_path), exist_ok=True)
    os.symlink(DOCS_SOURCE, link_path)
    return f"Symlink created: {link_path} -> {DOCS_SOURCE}"

mcp.run(transport="stdio")

