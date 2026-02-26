"""Unit tests for smarty_mcfly.commands.learn."""

import gzip
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, call, patch

import pytest

from smarty_mcfly.commands.learn import (
    _get_smarts_dir,
    _run_pandoc,
    _save_doc,
    _update_manifest,
    learn_godoc,
    learn_javadoc,
    learn_man,
    learn_rustdoc,
    learn_sphinx,
    learn_url,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

FAKE_MARKDOWN = "# Topic\n\nSome content.\n"


def _mock_httpx_get(mocker, text: str = "<html>Docs</html>", status: int = 200):
    mock_resp = MagicMock()
    mock_resp.text = text
    mock_resp.raise_for_status = MagicMock()
    return mocker.patch("smarty_mcfly.commands.learn.httpx.get", return_value=mock_resp)


def _mock_pandoc(mocker, output: str = FAKE_MARKDOWN):
    return mocker.patch("smarty_mcfly.commands.learn._run_pandoc", return_value=output)


# ---------------------------------------------------------------------------
# _get_smarts_dir
# ---------------------------------------------------------------------------


class TestGetSmartsDir:
    def test_returns_smarts_subdir_of_project_root(self, tmp_project):
        result = _get_smarts_dir(str(tmp_project))
        assert result == tmp_project / ".smarts"

    def test_resolves_relative_path(self):
        result = _get_smarts_dir(".")
        assert result.is_absolute()
        assert result.name == ".smarts"


# ---------------------------------------------------------------------------
# _run_pandoc
# ---------------------------------------------------------------------------


class TestRunPandoc:
    def test_calls_pandoc_with_correct_flags(self):
        mock_result = MagicMock(stdout=FAKE_MARKDOWN)
        with patch(
            "smarty_mcfly.commands.learn.subprocess.run", return_value=mock_result
        ) as mock_run:
            result = _run_pandoc("<h1>Hi</h1>", "html")

        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "pandoc"
        assert "-f" in cmd
        assert "html" in cmd
        assert "-t" in cmd
        assert "gfm" in cmd
        assert "--wrap=none" in cmd
        assert result == FAKE_MARKDOWN

    def test_passes_content_as_stdin(self):
        mock_result = MagicMock(stdout="output")
        with patch(
            "smarty_mcfly.commands.learn.subprocess.run", return_value=mock_result
        ) as mock_run:
            _run_pandoc("my content", "man")

        kwargs = mock_run.call_args[1]
        assert kwargs["input"] == "my content"

    def test_raises_on_pandoc_error(self):
        with patch(
            "smarty_mcfly.commands.learn.subprocess.run",
            side_effect=subprocess.CalledProcessError(1, "pandoc"),
        ):
            with pytest.raises(subprocess.CalledProcessError):
                _run_pandoc("content", "html")


# ---------------------------------------------------------------------------
# _update_manifest
# ---------------------------------------------------------------------------


class TestUpdateManifest:
    def test_creates_manifest_when_missing(self, smarts_dir):
        doc = smarts_dir / "python" / "requests.md"
        _update_manifest(smarts_dir, "python", "requests", doc)

        content = (smarts_dir / "MANIFEST.md").read_text()
        assert "## python" in content
        assert "requests" in content

    def test_adds_new_topic_section_to_existing_manifest(self, smarts_dir):
        (smarts_dir / "MANIFEST.md").write_text(
            "# Manifest\n\n## rust\n- [tokio](rust/tokio.md)\n"
        )
        doc = smarts_dir / "python" / "flask.md"
        _update_manifest(smarts_dir, "python", "flask", doc)

        content = (smarts_dir / "MANIFEST.md").read_text()
        assert "## rust" in content
        assert "## python" in content
        assert "flask" in content

    def test_adds_entry_under_existing_topic(self, smarts_dir):
        (smarts_dir / "MANIFEST.md").write_text(
            "# Manifest\n\n## python\n- [flask](python/flask.md)\n"
        )
        doc = smarts_dir / "python" / "requests.md"
        _update_manifest(smarts_dir, "python", "requests", doc)

        content = (smarts_dir / "MANIFEST.md").read_text()
        assert content.count("## python") == 1
        assert "flask" in content
        assert "requests" in content

    def test_does_not_duplicate_topic_header(self, smarts_dir):
        manifest = smarts_dir / "MANIFEST.md"
        manifest.write_text("# Manifest\n\n## go\n- [fmt](go/fmt.md)\n")
        doc = smarts_dir / "go" / "io.md"
        _update_manifest(smarts_dir, "go", "io", doc)

        assert manifest.read_text().count("## go") == 1


# ---------------------------------------------------------------------------
# _save_doc
# ---------------------------------------------------------------------------


class TestSaveDoc:
    def test_creates_topic_dir_and_file(self, smarts_dir):
        with patch("smarty_mcfly.commands.learn._update_manifest"):
            result = _save_doc(smarts_dir, "python", "requests", FAKE_MARKDOWN)

        doc = smarts_dir / "python" / "requests.md"
        assert doc.exists()
        assert doc.read_text() == FAKE_MARKDOWN
        assert "requests.md" in result

    def test_creates_smarts_dir_if_missing(self, tmp_project):
        smarts = tmp_project / ".smarts"
        assert not smarts.exists()
        with patch("smarty_mcfly.commands.learn._update_manifest"):
            _save_doc(smarts, "rust", "serde", "content")
        assert smarts.exists()

    def test_calls_update_manifest(self, smarts_dir):
        with patch("smarty_mcfly.commands.learn._update_manifest") as mock_update:
            _save_doc(smarts_dir, "go", "fmt", "content")
        mock_update.assert_called_once()
        args = mock_update.call_args[0]
        assert args[0] == smarts_dir
        assert args[1] == "go"
        assert args[2] == "fmt"


# ---------------------------------------------------------------------------
# learn_url
# ---------------------------------------------------------------------------


class TestLearnUrl:
    def test_fetches_url_and_saves_markdown(self, tmp_project, mocker):
        _mock_httpx_get(mocker)
        _mock_pandoc(mocker)

        result = learn_url("python", "requests", "https://example.com", str(tmp_project))

        doc = tmp_project / ".smarts" / "python" / "requests.md"
        assert doc.exists()
        assert "requests.md" in result

    def test_calls_httpx_with_follow_redirects(self, tmp_project, mocker):
        mock_get = _mock_httpx_get(mocker)
        _mock_pandoc(mocker)

        learn_url("python", "requests", "https://example.com", str(tmp_project))

        mock_get.assert_called_once_with(
            "https://example.com", follow_redirects=True
        )

    def test_raises_on_http_error(self, tmp_project, mocker):
        import httpx

        mocker.patch(
            "smarty_mcfly.commands.learn.httpx.get",
            side_effect=httpx.HTTPStatusError(
                "404", request=MagicMock(), response=MagicMock(status_code=404)
            ),
        )

        with pytest.raises(httpx.HTTPStatusError):
            learn_url("python", "requests", "https://example.com/404", str(tmp_project))


# ---------------------------------------------------------------------------
# learn_man
# ---------------------------------------------------------------------------


class TestLearnMan:
    def test_reads_plain_man_file(self, tmp_project, mocker):
        man_file = tmp_project / "ls.1"
        man_file.write_text(".TH LS 1\n.SH NAME\nls")

        def fake_run(cmd, **kwargs):
            mock = MagicMock()
            if "-w" in cmd:
                mock.stdout = str(man_file) + "\n"
            else:
                mock.stdout = FAKE_MARKDOWN
            return mock

        mocker.patch("smarty_mcfly.commands.learn.subprocess.run", side_effect=fake_run)
        result = learn_man("unix", "ls", "ls", str(tmp_project))
        assert "ls.md" in result

    def test_reads_gzipped_man_file(self, tmp_project, mocker):
        man_file = tmp_project / "ls.1.gz"
        content = ".TH LS 1\n.SH NAME\nls"
        man_file.write_bytes(gzip.compress(content.encode()))

        def fake_run(cmd, **kwargs):
            mock = MagicMock()
            if "-w" in cmd:
                mock.stdout = str(man_file) + "\n"
            else:
                mock.stdout = FAKE_MARKDOWN
            return mock

        mocker.patch("smarty_mcfly.commands.learn.subprocess.run", side_effect=fake_run)
        result = learn_man("unix", "ls", "ls", str(tmp_project))
        assert "ls.md" in result

    def test_passes_man_format_to_pandoc(self, tmp_project, mocker):
        man_file = tmp_project / "ls.1"
        man_file.write_text(".TH LS 1")

        pandoc_calls = []

        def fake_run(cmd, **kwargs):
            mock = MagicMock()
            if "-w" in cmd:
                mock.stdout = str(man_file) + "\n"
            else:
                pandoc_calls.append(cmd)
                mock.stdout = FAKE_MARKDOWN
            return mock

        mocker.patch("smarty_mcfly.commands.learn.subprocess.run", side_effect=fake_run)
        learn_man("unix", "ls", "ls", str(tmp_project))

        assert any("man" in str(c) for c in pandoc_calls[0])


# ---------------------------------------------------------------------------
# learn_javadoc
# ---------------------------------------------------------------------------


class TestLearnJavadoc:
    def test_passes_url_directly_to_httpx(self, tmp_project, mocker):
        url = "https://javadoc.example.com/api/"
        mock_get = _mock_httpx_get(mocker)
        _mock_pandoc(mocker)

        learn_javadoc("java", "mylib", url, str(tmp_project))

        mock_get.assert_called_once_with(url, follow_redirects=True)

    def test_constructs_javadoc_io_url_from_maven_coord(self, tmp_project, mocker):
        coord = "com.example:my-lib:1.0.0"
        expected = "https://javadoc.io/doc/com/example/my-lib/1.0.0"
        mock_get = _mock_httpx_get(mocker)
        _mock_pandoc(mocker)

        learn_javadoc("java", "my-lib", coord, str(tmp_project))

        mock_get.assert_called_once_with(expected, follow_redirects=True)

    def test_constructs_url_for_coord_without_version(self, tmp_project, mocker):
        coord = "org.example:lib"
        mock_get = _mock_httpx_get(mocker)
        _mock_pandoc(mocker)

        learn_javadoc("java", "lib", coord, str(tmp_project))

        url_used = mock_get.call_args[0][0]
        assert "javadoc.io" in url_used
        assert "org/example/lib" in url_used


# ---------------------------------------------------------------------------
# learn_sphinx
# ---------------------------------------------------------------------------


class TestLearnSphinx:
    def test_passes_url_directly_to_httpx(self, tmp_project, mocker):
        url = "https://myproject.readthedocs.io/en/stable/"
        mock_get = _mock_httpx_get(mocker)
        _mock_pandoc(mocker)

        learn_sphinx("python", "myproject", url, str(tmp_project))

        mock_get.assert_called_once_with(url, follow_redirects=True)

    def test_constructs_readthedocs_url_from_package_name(self, tmp_project, mocker):
        package = "requests"
        expected = "https://requests.readthedocs.io/en/latest/"
        mock_get = _mock_httpx_get(mocker)
        _mock_pandoc(mocker)

        learn_sphinx("python", "requests", package, str(tmp_project))

        mock_get.assert_called_once_with(expected, follow_redirects=True)


# ---------------------------------------------------------------------------
# learn_godoc
# ---------------------------------------------------------------------------


class TestLearnGodoc:
    def test_uses_go_doc_command_for_module_path(self, tmp_project, mocker):
        mock_result = MagicMock(stdout="Package fmt implements formatted I/O.")
        mocker.patch(
            "smarty_mcfly.commands.learn.subprocess.run", return_value=mock_result
        )

        result = learn_godoc("go", "fmt", "fmt", str(tmp_project))

        doc = tmp_project / ".smarts" / "go" / "fmt.md"
        assert doc.exists()
        assert "fmt.md" in result

    def test_falls_back_to_pkggodev_when_go_not_available(self, tmp_project, mocker):
        module = "github.com/some/pkg"
        expected_url = f"https://pkg.go.dev/{module}"

        mocker.patch(
            "smarty_mcfly.commands.learn.subprocess.run",
            side_effect=subprocess.CalledProcessError(1, "go"),
        )
        mock_get = _mock_httpx_get(mocker)
        _mock_pandoc(mocker)

        result = learn_godoc("go", "pkg", module, str(tmp_project))

        mock_get.assert_called_once_with(expected_url, follow_redirects=True)
        assert "pkg.md" in result

    def test_falls_back_when_go_not_installed(self, tmp_project, mocker):
        module = "github.com/gorilla/mux"
        mocker.patch(
            "smarty_mcfly.commands.learn.subprocess.run",
            side_effect=FileNotFoundError("go not found"),
        )
        mock_get = _mock_httpx_get(mocker)
        _mock_pandoc(mocker)

        learn_godoc("go", "mux", module, str(tmp_project))

        mock_get.assert_called_once()

    def test_uses_url_directly_when_starts_with_http(self, tmp_project, mocker):
        url = "https://pkg.go.dev/fmt"
        mock_get = _mock_httpx_get(mocker)
        _mock_pandoc(mocker)

        learn_godoc("go", "fmt", url, str(tmp_project))

        mock_get.assert_called_once_with(url, follow_redirects=True)


# ---------------------------------------------------------------------------
# learn_rustdoc
# ---------------------------------------------------------------------------


class TestLearnRustdoc:
    def test_passes_url_directly_to_httpx(self, tmp_project, mocker):
        url = "https://docs.rs/serde/1.0/serde/"
        mock_get = _mock_httpx_get(mocker)
        _mock_pandoc(mocker)

        learn_rustdoc("rust", "serde", url, str(tmp_project))

        mock_get.assert_called_once_with(url, follow_redirects=True)

    def test_constructs_docs_rs_url_from_crate_name(self, tmp_project, mocker):
        crate = "serde"
        expected = "https://docs.rs/serde/latest/serde/"
        mock_get = _mock_httpx_get(mocker)
        _mock_pandoc(mocker)

        learn_rustdoc("rust", "serde", crate, str(tmp_project))

        mock_get.assert_called_once_with(expected, follow_redirects=True)

    def test_converts_hyphens_to_underscores_in_module_path(self, tmp_project, mocker):
        crate = "my-crate"
        expected = "https://docs.rs/my-crate/latest/my_crate/"
        mock_get = _mock_httpx_get(mocker)
        _mock_pandoc(mocker)

        learn_rustdoc("rust", "my-crate", crate, str(tmp_project))

        mock_get.assert_called_once_with(expected, follow_redirects=True)

    def test_saves_markdown_to_correct_path(self, tmp_project, mocker):
        _mock_httpx_get(mocker)
        _mock_pandoc(mocker, output="# Serde\n\nA serialization framework.\n")

        result = learn_rustdoc("rust", "serde", "serde", str(tmp_project))

        doc = tmp_project / ".smarts" / "rust" / "serde.md"
        assert doc.exists()
        assert doc.read_text() == "# Serde\n\nA serialization framework.\n"
        assert "serde.md" in result
