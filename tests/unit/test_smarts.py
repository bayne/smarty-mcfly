"""Unit tests for smarty_mcfly.commands.smarts."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from smarty_mcfly.commands.smarts import REPO_URL, SMARTS_DIR, ensure_smarts


def _make_fake_clone(tmp_path: Path, *, include_smarts: bool = True):
    """Return a fake subprocess.run that populates the cloned repo directory."""

    def fake_clone(cmd, **kwargs):
        # git clone's last positional arg is the destination
        dest = Path(cmd[-1])
        dest.mkdir(parents=True, exist_ok=True)
        if include_smarts:
            smarts = dest / SMARTS_DIR
            smarts.mkdir()
            (smarts / "MANIFEST.md").write_text("# Smarts\n")
        return MagicMock(returncode=0)

    return fake_clone


class TestEnsureSmarts:
    def test_returns_early_when_already_exists(self, tmp_project):
        (tmp_project / ".smarts").mkdir()
        with patch("smarty_mcfly.commands.smarts.subprocess.run") as mock_run:
            result = ensure_smarts(str(tmp_project))
        mock_run.assert_not_called()
        assert "already available" in result
        assert ".smarts" in result

    def test_clones_repo_and_copies_smarts(self, tmp_project):
        with patch(
            "smarty_mcfly.commands.smarts.subprocess.run",
            side_effect=_make_fake_clone(tmp_project),
        ):
            result = ensure_smarts(str(tmp_project))

        target = tmp_project / ".smarts"
        assert target.exists()
        assert (target / "MANIFEST.md").read_text() == "# Smarts\n"
        assert "cloned to" in result
        assert str(target) in result

    def test_uses_correct_repo_url_and_depth(self, tmp_project):
        clone_cmd = []

        def capture_clone(cmd, **kwargs):
            clone_cmd.extend(cmd)
            dest = Path(cmd[-1])
            dest.mkdir(parents=True, exist_ok=True)
            (dest / SMARTS_DIR).mkdir()
            return MagicMock(returncode=0)

        with patch("smarty_mcfly.commands.smarts.subprocess.run", side_effect=capture_clone):
            ensure_smarts(str(tmp_project))

        assert REPO_URL in clone_cmd
        assert "--depth=1" in clone_cmd

    def test_raises_on_clone_failure(self, tmp_project):
        with patch(
            "smarty_mcfly.commands.smarts.subprocess.run",
            side_effect=subprocess.CalledProcessError(
                128, "git", stderr="Permission denied (publickey)."
            ),
        ):
            with pytest.raises(RuntimeError, match="Permission denied"):
                ensure_smarts(str(tmp_project))

    def test_raises_when_smarts_dir_missing_from_repo(self, tmp_project):
        with patch(
            "smarty_mcfly.commands.smarts.subprocess.run",
            side_effect=_make_fake_clone(tmp_project, include_smarts=False),
        ):
            with pytest.raises(RuntimeError, match="does not contain"):
                ensure_smarts(str(tmp_project))

    def test_does_not_leave_temp_clone_on_success(self, tmp_project):
        with patch(
            "smarty_mcfly.commands.smarts.subprocess.run",
            side_effect=_make_fake_clone(tmp_project),
        ):
            ensure_smarts(str(tmp_project))

        # Only .smarts should exist, no leftover temp directories
        children = [p for p in tmp_project.iterdir() if p.name != ".smarts"]
        assert children == []
