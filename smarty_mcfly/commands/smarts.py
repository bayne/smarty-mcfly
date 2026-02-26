"""Clone the smarts documentation directory into the project."""

import shutil
import subprocess
import tempfile
from pathlib import Path

REPO_URL = "git@github.com:bayne/smarty-mcfly.git"
SMARTS_DIR = "smarts"
TARGET_DIR = ".smarts"


def ensure_smarts(project_root: str = ".") -> str:
    """Clone the smarts directory into .smarts if it doesn't exist.

    Clones only the smarts/ directory from the smarty-mcfly repository
    into .smarts/ in the given project root.
    """
    project_path = Path(project_root).resolve()
    target_path = project_path / TARGET_DIR

    if target_path.exists():
        return f"Smarts already available at {target_path}"

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            subprocess.run(
                ["git", "clone", "--depth=1", REPO_URL, tmpdir],
                check=True,
                capture_output=True,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to clone repository: {e.stderr}") from e

        smarts_source = Path(tmpdir) / SMARTS_DIR
        if not smarts_source.exists():
            raise RuntimeError(
                f"Repository does not contain a '{SMARTS_DIR}' directory"
            )

        shutil.copytree(smarts_source, target_path)

    return f"Smarts cloned to {target_path}"
