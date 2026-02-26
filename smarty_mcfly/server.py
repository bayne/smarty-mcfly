"""MCP server for smarty-mcfly.

All tools here are also available as direct CLI commands.
"""

from fastmcp import FastMCP

from .commands import learn as learn_cmd
from .commands import smarts as smarts_cmd

mcp = FastMCP("smarty-mcfly")


@mcp.tool()
def setup_smarts(project_root: str = ".") -> str:
    """Clone the .smarts documentation directory into the project if it doesn't exist.

    Clones the smarts/ directory from the smarty-mcfly repository into .smarts/
    in the specified project root. Safe to call multiple times.
    """
    return smarts_cmd.ensure_smarts(project_root)


@mcp.tool()
def learn_from_url(
    topic: str, subtopic: str, url: str, project_root: str = "."
) -> str:
    """Fetch a web page and save it as markdown documentation in .smarts/.

    Uses pandoc to convert the HTML to GitHub Flavored Markdown.
    Updates .smarts/MANIFEST.md with the new topic entry.
    """
    return learn_cmd.learn_url(topic, subtopic, url, project_root)


@mcp.tool()
def learn_from_man(
    topic: str, subtopic: str, man_page: str, project_root: str = "."
) -> str:
    """Convert a man page to markdown and save it in .smarts/.

    Uses pandoc to convert the man page source to GitHub Flavored Markdown.
    Updates .smarts/MANIFEST.md with the new topic entry.
    """
    return learn_cmd.learn_man(topic, subtopic, man_page, project_root)


@mcp.tool()
def learn_from_javadoc(
    topic: str, subtopic: str, package_id: str, project_root: str = "."
) -> str:
    """Fetch JavaDoc and save it as markdown in .smarts/.

    package_id can be a full URL or a Maven coordinate (group:artifact:version).
    Updates .smarts/MANIFEST.md with the new topic entry.
    """
    return learn_cmd.learn_javadoc(topic, subtopic, package_id, project_root)


@mcp.tool()
def learn_from_sphinx(
    topic: str, subtopic: str, package_id: str, project_root: str = "."
) -> str:
    """Fetch Python Sphinx docs and save as markdown in .smarts/.

    package_id can be a full URL or a PyPI package name (fetched from ReadTheDocs).
    Updates .smarts/MANIFEST.md with the new topic entry.
    """
    return learn_cmd.learn_sphinx(topic, subtopic, package_id, project_root)


@mcp.tool()
def learn_from_godoc(
    topic: str, subtopic: str, module: str, project_root: str = "."
) -> str:
    """Fetch Go documentation and save as markdown in .smarts/.

    module can be a full URL or a Go module path (uses go doc or pkg.go.dev).
    Updates .smarts/MANIFEST.md with the new topic entry.
    """
    return learn_cmd.learn_godoc(topic, subtopic, module, project_root)


@mcp.tool()
def learn_from_rustdoc(
    topic: str, subtopic: str, crate: str, project_root: str = "."
) -> str:
    """Fetch Rust documentation and save as markdown in .smarts/.

    crate can be a full URL or a crate name (fetched from docs.rs).
    Updates .smarts/MANIFEST.md with the new topic entry.
    """
    return learn_cmd.learn_rustdoc(topic, subtopic, crate, project_root)


def main() -> None:
    mcp.run(transport="stdio")
