from __future__ import annotations

import importlib.util
import io
import sys
import tarfile
import zipfile
from pathlib import Path
from typing import Any

import pytest


def _load_compile_module() -> Any:
    script = (
        Path(__file__).parents[2]
        / "skills"
        / "tailor-latex-cv"
        / "scripts"
        / "compile_latex.py"
    )
    spec = importlib.util.spec_from_file_location("compile_latex_skill", script)
    if spec is None or spec.loader is None:
        raise AssertionError(f"Unable to load {script}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


compile_latex = _load_compile_module()


def test_selects_pinned_windows_asset() -> None:
    asset = compile_latex._select_asset("Windows", "AMD64", "default")

    assert asset.filename == "tectonic-0.16.9-x86_64-pc-windows-msvc.zip"
    assert len(asset.sha256) == 64


def test_rejects_unsupported_platform() -> None:
    with pytest.raises(compile_latex.CvCompilationError, match="No pinned"):
        compile_latex._select_asset("Plan9", "mips", "default")


def test_extracts_only_tectonic_from_zip(tmp_path: Path, monkeypatch: Any) -> None:
    archive_path = tmp_path / "tectonic.zip"
    destination = tmp_path / "tectonic.exe"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("nested/tectonic.exe", b"binary")
        archive.writestr("nested/unrelated.txt", b"ignored")
    monkeypatch.setattr(compile_latex, "_executable_name", lambda: "tectonic.exe")

    compile_latex._extract_binary(archive_path, destination)

    assert destination.read_bytes() == b"binary"


def test_extracts_only_tectonic_from_tar(tmp_path: Path, monkeypatch: Any) -> None:
    archive_path = tmp_path / "tectonic.tar.gz"
    destination = tmp_path / "tectonic"
    payload = b"binary"
    with tarfile.open(archive_path, "w:gz") as archive:
        member = tarfile.TarInfo("nested/tectonic")
        member.size = len(payload)
        archive.addfile(member, io.BytesIO(payload))
    monkeypatch.setattr(compile_latex, "_executable_name", lambda: "tectonic")

    compile_latex._extract_binary(archive_path, destination)

    assert destination.read_bytes() == payload


def test_rejects_hidden_text_techniques(tmp_path: Path) -> None:
    source = tmp_path / "cv.tex"
    source.write_text(r"\textcolor{white}{keyword}", encoding="utf-8")

    with pytest.raises(compile_latex.CvCompilationError, match="hidden-text"):
        compile_latex._validate_source(source)


def test_rejects_fontawesome_on_windows_before_compilation(tmp_path: Path) -> None:
    source = tmp_path / "cv.tex"
    source.write_text(r"\usepackage{fontawesome5}", encoding="utf-8")

    with pytest.raises(compile_latex.CvCompilationError, match="fontawesome5"):
        compile_latex._validate_source(source, system="Windows")


def test_normalizes_extracted_pdf_text() -> None:
    assert compile_latex._normalize_text("  REST\n APIs  ") == "rest apis"


def test_creates_isolated_windows_fontconfig(tmp_path: Path) -> None:
    environment: dict[str, str] = {}

    compile_latex._configure_fontconfig(environment, tmp_path, system="Windows")

    config_path = Path(environment["FONTCONFIG_FILE"])
    assert config_path.is_file()
    assert "fontconfig-cache" in config_path.read_text(encoding="utf-8")


def test_publishes_validated_pdf_atomically(tmp_path: Path) -> None:
    build_pdf = tmp_path / "build" / "cv.pdf"
    build_pdf.parent.mkdir()
    build_pdf.write_bytes(b"%PDF-validated")
    final_pdf = tmp_path / "cv.pdf"

    published_pdf = compile_latex._publish_pdf(build_pdf, final_pdf)

    assert published_pdf == final_pdf
    assert final_pdf.read_bytes() == b"%PDF-validated"
    assert list(tmp_path.glob(".*.tmp")) == []


def test_does_not_overwrite_existing_final_pdf(tmp_path: Path) -> None:
    build_pdf = tmp_path / "build" / "cv.pdf"
    build_pdf.parent.mkdir()
    build_pdf.write_bytes(b"%PDF-new")
    final_pdf = tmp_path / "cv.pdf"
    final_pdf.write_bytes(b"%PDF-existing")

    published_pdf = compile_latex._publish_pdf(build_pdf, final_pdf)

    assert published_pdf == tmp_path / "cv-2.pdf"
    assert final_pdf.read_bytes() == b"%PDF-existing"
    assert published_pdf.read_bytes() == b"%PDF-new"


def test_rejects_non_pdf_final_path(tmp_path: Path) -> None:
    build_pdf = tmp_path / "build.pdf"
    build_pdf.write_bytes(b"%PDF-validated")

    with pytest.raises(compile_latex.CvCompilationError, match=".pdf extension"):
        compile_latex._publish_pdf(build_pdf, tmp_path / "cv.txt")


def test_does_not_publish_when_pdf_validation_fails(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    source = tmp_path / "cv.tex"
    source.write_text(r"\documentclass{article}", encoding="utf-8")
    build_pdf = tmp_path / "build" / "cv.pdf"
    build_pdf.parent.mkdir()
    build_pdf.write_bytes(b"%PDF-invalid")
    final_pdf = tmp_path / "cv.pdf"
    publish_called = False

    monkeypatch.setattr(
        compile_latex,
        "_find_tectonic",
        lambda *_arguments: tmp_path / "tectonic",
    )
    monkeypatch.setattr(compile_latex, "_probe_compiler", lambda _path: "test")
    monkeypatch.setattr(
        compile_latex,
        "_compile",
        lambda *_arguments: (build_pdf, object()),
    )

    def reject_pdf(*_arguments: Any) -> None:
        raise compile_latex.CvCompilationError("PDF validation failed")

    def record_publish(*_arguments: Any, **_keywords: Any) -> Path:
        nonlocal publish_called
        publish_called = True
        return final_pdf

    monkeypatch.setattr(compile_latex, "_verify_pdf", reject_pdf)
    monkeypatch.setattr(compile_latex, "_publish_pdf", record_publish)

    result = compile_latex.main([str(source), "--final-pdf", str(final_pdf)])

    assert result == 1
    assert publish_called is False
    assert not final_pdf.exists()
