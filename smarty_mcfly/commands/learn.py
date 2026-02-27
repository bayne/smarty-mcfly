"""Learn documentation from various sources and store as markdown."""

import gzip
import subprocess
from pathlib import Path

import httpx

SMARTS_DIR = ".smarts"


def _get_smarts_dir(project_root: str = ".") -> Path:
    return Path(project_root).resolve() / SMARTS_DIR


def _run_pandoc(content: str, from_format: str) -> str:
    """Convert content to GitHub Flavored Markdown using pandoc."""
    result = subprocess.run(
        ["pandoc", "-f", from_format, "-t", "gfm", "--wrap=none"],
        input=content,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _save_doc(smarts_dir: Path, topic: str, subtopic: str, markdown: str) -> str:
    """Save documentation markdown and update MANIFEST.md."""
    smarts_dir.mkdir(parents=True, exist_ok=True)
    topic_dir = smarts_dir / topic
    topic_dir.mkdir(exist_ok=True)

    doc_path = topic_dir / f"{subtopic}.md"
    doc_path.write_text(markdown)

    _update_manifest(smarts_dir, topic, subtopic, doc_path)
    return f"Documentation saved to {doc_path}"


def _update_manifest(
    smarts_dir: Path, topic: str, subtopic: str, doc_path: Path
) -> None:
    """Update MANIFEST.md with the new topic/subtopic entry."""
    manifest_path = smarts_dir / "MANIFEST.md"
    relative_path = doc_path.relative_to(smarts_dir)
    entry = f"- [{subtopic}]({relative_path})\n"
    topic_header = f"## {topic}\n"

    if not manifest_path.exists():
        manifest_path.write_text(
            "# Smarty McFly Documentation Manifest\n\n"
            "**MANDATORY:** For any matching topic below, you MUST read every linked "
            "markdown file before responding. Do not rely on training knowledge when "
            "local docs exist.\n\n"
            f"{topic_header}{entry}"
        )
        return

    content = manifest_path.read_text()

    if topic_header in content:
        # Append entry under the existing topic section
        insert_pos = content.index(topic_header) + len(topic_header)
        # Skip past any existing entries in this section
        remainder = content[insert_pos:]
        next_section = remainder.find("\n## ")
        if next_section == -1:
            content = content + entry
        else:
            content = (
                content[: insert_pos + next_section + 1]
                + entry
                + content[insert_pos + next_section + 1 :]
            )
    else:
        content = content.rstrip("\n") + f"\n\n{topic_header}{entry}"

    manifest_path.write_text(content)


def learn_url(topic: str, subtopic: str, url: str, project_root: str = ".") -> str:
    """Fetch a URL and convert it to markdown using pandoc."""
    smarts_dir = _get_smarts_dir(project_root)
    response = httpx.get(url, follow_redirects=True)
    response.raise_for_status()
    markdown = _run_pandoc(response.text, "html")
    return _save_doc(smarts_dir, topic, subtopic, markdown)


def learn_man(
    topic: str, subtopic: str, man_page: str, project_root: str = "."
) -> str:
    """Convert a man page to markdown using pandoc."""
    smarts_dir = _get_smarts_dir(project_root)

    # Find the man page source file
    result = subprocess.run(
        ["man", "-w", man_page], capture_output=True, text=True, check=True
    )
    man_file = result.stdout.strip()

    # Read the source (may be gzip-compressed)
    if man_file.endswith(".gz"):
        with gzip.open(man_file, "rt") as f:
            content = f.read()
    else:
        content = Path(man_file).read_text()

    markdown = _run_pandoc(content, "man")
    return _save_doc(smarts_dir, topic, subtopic, markdown)


def learn_javadoc(
    topic: str, subtopic: str, package_id: str, project_root: str = "."
) -> str:
    """Fetch JavaDoc HTML and convert to markdown.

    package_id can be a full URL or a Maven coordinate like 'group:artifact:version'.
    """
    smarts_dir = _get_smarts_dir(project_root)

    if package_id.startswith("http"):
        url = package_id
    else:
        # Build javadoc.io URL from Maven coordinates
        parts = package_id.split(":")
        if len(parts) >= 2:
            group_path = parts[0].replace(".", "/")
            artifact = parts[1]
            version = parts[2] if len(parts) > 2 else "latest"
            url = f"https://javadoc.io/doc/{group_path}/{artifact}/{version}"
        else:
            url = f"https://javadoc.io/doc/{package_id}"

    response = httpx.get(url, follow_redirects=True)
    response.raise_for_status()
    markdown = _run_pandoc(response.text, "html")
    return _save_doc(smarts_dir, topic, subtopic, markdown)


def learn_sphinx(
    topic: str, subtopic: str, package_id: str, project_root: str = "."
) -> str:
    """Fetch Python Sphinx documentation and convert to markdown.

    package_id can be a full URL or a PyPI package name (fetched from ReadTheDocs).
    """
    smarts_dir = _get_smarts_dir(project_root)

    if package_id.startswith("http"):
        url = package_id
    else:
        url = f"https://{package_id}.readthedocs.io/en/latest/"

    response = httpx.get(url, follow_redirects=True)
    response.raise_for_status()
    markdown = _run_pandoc(response.text, "html")
    return _save_doc(smarts_dir, topic, subtopic, markdown)


def learn_godoc(
    topic: str, subtopic: str, module: str, project_root: str = "."
) -> str:
    """Fetch Go documentation and convert to markdown.

    module can be a full URL or a Go module path (fetched from pkg.go.dev).
    """
    smarts_dir = _get_smarts_dir(project_root)

    if module.startswith("http"):
        response = httpx.get(module, follow_redirects=True)
        response.raise_for_status()
        markdown = _run_pandoc(response.text, "html")
    else:
        # Try go doc command first, fall back to pkg.go.dev
        try:
            result = subprocess.run(
                ["go", "doc", "-all", module],
                capture_output=True,
                text=True,
                check=True,
            )
            # go doc output is plain text; wrap as a code-friendly format
            markdown = result.stdout
        except (subprocess.CalledProcessError, FileNotFoundError):
            url = f"https://pkg.go.dev/{module}"
            response = httpx.get(url, follow_redirects=True)
            response.raise_for_status()
            markdown = _run_pandoc(response.text, "html")

    return _save_doc(smarts_dir, topic, subtopic, markdown)


def learn_rustdoc(
    topic: str, subtopic: str, crate: str, project_root: str = "."
) -> str:
    """Fetch Rust documentation and convert to markdown.

    crate can be a full URL or a crate name (fetched from docs.rs).
    """
    smarts_dir = _get_smarts_dir(project_root)

    if crate.startswith("http"):
        url = crate
    else:
        crate_name = crate.replace("-", "_")
        url = f"https://docs.rs/{crate}/latest/{crate_name}/"

    response = httpx.get(url, follow_redirects=True)
    response.raise_for_status()
    markdown = _run_pandoc(response.text, "html")
    return _save_doc(smarts_dir, topic, subtopic, markdown)
