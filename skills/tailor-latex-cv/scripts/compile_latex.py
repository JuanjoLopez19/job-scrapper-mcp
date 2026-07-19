# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pypdf==6.14.2",
# ]
# ///

"""Install a pinned Tectonic binary, compile a LaTeX CV, and verify its PDF."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
import tarfile
import tempfile
import zipfile
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import IO
from urllib.error import URLError
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape

from pypdf import PdfReader

TECTONIC_VERSION = "0.16.9"
RELEASE_BASE_URL = (
    "https://github.com/tectonic-typesetting/tectonic/releases/download/"
    f"tectonic%40{TECTONIC_VERSION}"
)
DEFAULT_BUNDLE_URL = "https://data1.fullyjustified.net/tlextras-2022.0r0.tar"
MAX_DOWNLOAD_BYTES = 100 * 1024 * 1024


class CvCompilationError(RuntimeError):
    """Raised when installation, compilation, or verification fails."""


@dataclass(frozen=True, slots=True)
class ReleaseAsset:
    filename: str
    sha256: str

    @property
    def url(self) -> str:
        return f"{RELEASE_BASE_URL}/{self.filename}"


@dataclass(frozen=True, slots=True)
class PdfReport:
    path: Path
    pages: int
    extracted_characters: int
    expected_keywords: tuple[str, ...]


ASSETS: dict[tuple[str, str, str], ReleaseAsset] = {
    (
        "Darwin",
        "aarch64",
        "default",
    ): ReleaseAsset(
        "tectonic-0.16.9-aarch64-apple-darwin.tar.gz",
        "edb67c61aba768289f6da441c9e6f523cfaff4f8b2a5708523ef29c543f8e88e",
    ),
    (
        "Darwin",
        "x86_64",
        "default",
    ): ReleaseAsset(
        "tectonic-0.16.9-x86_64-apple-darwin.tar.gz",
        "79d8839fa3594bfea9b2bf2ac0a0455bcc4d0de956a5e5c403107e9a72f79e86",
    ),
    (
        "Linux",
        "aarch64",
        "gnu",
    ): ReleaseAsset(
        "tectonic-0.16.9-aarch64-unknown-linux-musl.tar.gz",
        "f9aa39017dbd51f111fdb93dda222178cbe51c8193508fc567b523cc74fff9c1",
    ),
    (
        "Linux",
        "aarch64",
        "musl",
    ): ReleaseAsset(
        "tectonic-0.16.9-aarch64-unknown-linux-musl.tar.gz",
        "f9aa39017dbd51f111fdb93dda222178cbe51c8193508fc567b523cc74fff9c1",
    ),
    (
        "Linux",
        "x86_64",
        "gnu",
    ): ReleaseAsset(
        "tectonic-0.16.9-x86_64-unknown-linux-gnu.tar.gz",
        "f3c825128095dc3399ea11c08c18035b33050a216930c295c79e8eb11bd21de4",
    ),
    (
        "Linux",
        "x86_64",
        "musl",
    ): ReleaseAsset(
        "tectonic-0.16.9-x86_64-unknown-linux-musl.tar.gz",
        "60b13a0826ae7ad9ce34b4a2df06bff2cfcfa6dda8a915477c0cbb84e1a4a902",
    ),
    (
        "Windows",
        "x86_64",
        "default",
    ): ReleaseAsset(
        "tectonic-0.16.9-x86_64-pc-windows-msvc.zip",
        "131a24604785a9600989a3d91225f597df52ac06f00aeffe86fd529f99ee5cdd",
    ),
}

HIDDEN_TEXT_PATTERNS = (
    r"\color{white}",
    r"\textcolor{white}",
    r"\fontsize{0}",
    r"\phantom",
)


def _normalize_machine(machine: str) -> str:
    normalized = machine.casefold()
    if normalized in {"amd64", "x64", "x86_64"}:
        return "x86_64"
    if normalized in {"aarch64", "arm64"}:
        return "aarch64"
    return normalized


def _linux_libc() -> str:
    libc_name, _ = platform.libc_ver()
    if "musl" in libc_name.casefold() or Path("/etc/alpine-release").exists():
        return "musl"
    return "gnu"


def _select_asset(
    system: str | None = None,
    machine: str | None = None,
    libc: str | None = None,
) -> ReleaseAsset:
    selected_system = system or platform.system()
    selected_machine = _normalize_machine(machine or platform.machine())
    selected_libc = libc or (_linux_libc() if selected_system == "Linux" else "default")
    key = (selected_system, selected_machine, selected_libc)
    try:
        return ASSETS[key]
    except KeyError as error:
        raise CvCompilationError(
            "No pinned Tectonic binary is available for "
            f"{selected_system}/{selected_machine}/{selected_libc}."
        ) from error


def _default_cache_dir() -> Path:
    if os.name == "nt":
        base = Path(
            os.environ.get(
                "LOCALAPPDATA",
                Path.home() / "AppData" / "Local",
            )
        )
    else:
        base = Path(os.environ.get("XDG_CACHE_HOME", Path.home() / ".cache"))
    return base / "tailor-latex-cv" / "tectonic" / TECTONIC_VERSION


def _executable_name() -> str:
    return "tectonic.exe" if os.name == "nt" else "tectonic"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download_asset(asset: ReleaseAsset, destination: Path) -> None:
    request = Request(asset.url, headers={"User-Agent": "tailor-latex-cv/1"})
    digest = hashlib.sha256()
    downloaded = 0
    try:
        with urlopen(request, timeout=60) as response, destination.open("wb") as file:
            while chunk := response.read(1024 * 1024):
                downloaded += len(chunk)
                if downloaded > MAX_DOWNLOAD_BYTES:
                    raise CvCompilationError(
                        "The Tectonic archive exceeded the 100 MiB safety limit."
                    )
                digest.update(chunk)
                file.write(chunk)
    except (OSError, URLError) as error:
        destination.unlink(missing_ok=True)
        raise CvCompilationError(
            f"Unable to download Tectonic from {asset.url}: {error}"
        ) from error

    actual_hash = digest.hexdigest()
    if actual_hash != asset.sha256:
        destination.unlink(missing_ok=True)
        raise CvCompilationError(
            "Tectonic archive SHA-256 mismatch: "
            f"expected {asset.sha256}, received {actual_hash}."
        )


def _copy_stream(source: IO[bytes], destination: Path) -> None:
    with destination.open("wb") as output:
        shutil.copyfileobj(source, output)


def _extract_binary(archive_path: Path, destination: Path) -> None:
    wanted_name = _executable_name()
    if archive_path.name.endswith(".zip"):
        with zipfile.ZipFile(archive_path) as archive:
            candidates = [
                name
                for name in archive.namelist()
                if PurePosixPath(name).name == wanted_name
            ]
            if len(candidates) != 1:
                raise CvCompilationError(
                    f"Expected one {wanted_name} in {archive_path.name}."
                )
            with archive.open(candidates[0]) as source:
                _copy_stream(source, destination)
    elif archive_path.name.endswith(".tar.gz"):
        with tarfile.open(archive_path, mode="r:gz") as archive:
            candidates = [
                member
                for member in archive.getmembers()
                if member.isfile() and PurePosixPath(member.name).name == wanted_name
            ]
            if len(candidates) != 1:
                raise CvCompilationError(
                    f"Expected one {wanted_name} in {archive_path.name}."
                )
            source = archive.extractfile(candidates[0])
            if source is None:
                raise CvCompilationError(f"Unable to read {wanted_name} from archive.")
            with source:
                _copy_stream(source, destination)
    else:
        raise CvCompilationError(f"Unsupported Tectonic archive: {archive_path.name}")

    destination.chmod(destination.stat().st_mode | stat.S_IXUSR)


def _probe_compiler(executable: Path) -> str:
    try:
        completed = subprocess.run(
            [str(executable), "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        raise CvCompilationError(
            f"Unable to execute the Tectonic binary at {executable}: {error}"
        ) from error
    if completed.returncode != 0:
        details = (completed.stderr or completed.stdout).strip()
        raise CvCompilationError(
            f"Tectonic probe failed with exit code {completed.returncode}: {details}"
        )
    return completed.stdout.strip() or completed.stderr.strip()


def _install_tectonic(cache_dir: Path) -> Path:
    asset = _select_asset()
    cache_dir.mkdir(parents=True, exist_ok=True)
    executable = cache_dir / _executable_name()
    if executable.exists():
        _probe_compiler(executable)
        return executable

    with tempfile.TemporaryDirectory(
        prefix="tectonic-download-",
        dir=cache_dir,
    ) as temporary_directory:
        temporary_path = Path(temporary_directory)
        archive_path = temporary_path / asset.filename
        candidate = temporary_path / _executable_name()
        _download_asset(asset, archive_path)
        _extract_binary(archive_path, candidate)
        _probe_compiler(candidate)
        candidate.replace(executable)
    return executable


def _find_tectonic(explicit: Path | None, cache_dir: Path) -> Path | None:
    if explicit is not None:
        explicit_path = explicit.expanduser().resolve()
        if not explicit_path.is_file():
            raise CvCompilationError(
                f"The requested Tectonic executable does not exist: {explicit_path}"
            )
        _probe_compiler(explicit_path)
        return explicit_path

    system_binary = shutil.which("tectonic")
    if system_binary:
        system_path = Path(system_binary).resolve()
        _probe_compiler(system_path)
        return system_path

    cached_binary = cache_dir / _executable_name()
    if cached_binary.is_file():
        _probe_compiler(cached_binary)
        return cached_binary
    return None


def _validate_source(source: Path, system: str | None = None) -> None:
    if not source.is_file():
        raise CvCompilationError(f"LaTeX source not found: {source}")
    if source.suffix.casefold() != ".tex":
        raise CvCompilationError(f"Expected a .tex source file, received: {source}")
    content = source.read_text(encoding="utf-8")
    matches = [pattern for pattern in HIDDEN_TEXT_PATTERNS if pattern in content]
    if matches:
        raise CvCompilationError(
            "Potential hidden-text technique detected in LaTeX source: "
            + ", ".join(matches)
        )
    if (
        system or platform.system()
    ) == "Windows" and r"\usepackage{fontawesome5}" in content:
        raise CvCompilationError(
            "fontawesome5 is incompatible with the pinned Windows Tectonic "
            "binary. Replace decorative icon commands with visible text labels "
            "in the tailored CV, then compile again."
        )


def _normalize_text(value: str) -> str:
    return " ".join(value.casefold().split())


def _configure_fontconfig(
    environment: dict[str, str],
    cache_dir: Path,
    system: str | None = None,
) -> None:
    if (system or platform.system()) != "Windows":
        return
    font_cache = cache_dir / "fontconfig-cache"
    font_cache.mkdir(parents=True, exist_ok=True)
    config_path = cache_dir / "fonts.conf"
    windows_fonts = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
    config_path.write_text(
        "\n".join(
            (
                '<?xml version="1.0"?>',
                '<!DOCTYPE fontconfig SYSTEM "urn:fontconfig:fonts.dtd">',
                "<fontconfig>",
                f"  <dir>{escape(windows_fonts.as_posix())}</dir>",
                f"  <cachedir>{escape(font_cache.as_posix())}</cachedir>",
                "</fontconfig>",
                "",
            )
        ),
        encoding="utf-8",
    )
    environment["FONTCONFIG_FILE"] = str(config_path)


def _verify_pdf(
    pdf_path: Path,
    expected_keywords: Sequence[str],
    forbidden_keywords: Sequence[str],
) -> PdfReport:
    if not pdf_path.is_file() or pdf_path.stat().st_size == 0:
        raise CvCompilationError(f"Expected PDF was not generated: {pdf_path}")
    try:
        reader = PdfReader(pdf_path, strict=False)
        extracted_text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as error:
        raise CvCompilationError(f"Unable to read generated PDF: {error}") from error

    normalized_text = _normalize_text(extracted_text)
    if not normalized_text:
        raise CvCompilationError("The generated PDF contains no extractable text.")

    missing = [
        keyword
        for keyword in expected_keywords
        if _normalize_text(keyword) not in normalized_text
    ]
    forbidden = [
        keyword
        for keyword in forbidden_keywords
        if _normalize_text(keyword) in normalized_text
    ]
    if missing:
        raise CvCompilationError(
            "Expected visible keywords were not extractable from the PDF: "
            + ", ".join(missing)
        )
    if forbidden:
        raise CvCompilationError(
            "Unsupported keywords were found in the generated PDF: "
            + ", ".join(forbidden)
        )

    return PdfReport(
        path=pdf_path,
        pages=len(reader.pages),
        extracted_characters=len(extracted_text.strip()),
        expected_keywords=tuple(expected_keywords),
    )


def _next_available_pdf_path(requested_path: Path) -> Path:
    if not requested_path.exists():
        return requested_path

    suffix_number = 2
    while True:
        candidate = requested_path.with_name(
            f"{requested_path.stem}-{suffix_number}{requested_path.suffix}"
        )
        if not candidate.exists():
            return candidate
        suffix_number += 1


def _publish_pdf(
    validated_pdf: Path,
    requested_path: Path,
    *,
    overwrite: bool = False,
) -> Path:
    if not validated_pdf.is_file() or validated_pdf.stat().st_size == 0:
        raise CvCompilationError(
            f"Validated build PDF is missing or empty: {validated_pdf}"
        )
    if requested_path.suffix.lower() != ".pdf":
        raise CvCompilationError("The final PDF path must use the .pdf extension.")

    validated_pdf = validated_pdf.resolve()
    requested_path = requested_path.resolve()
    if validated_pdf == requested_path:
        return validated_pdf

    final_path = (
        requested_path if overwrite else _next_available_pdf_path(requested_path)
    )
    final_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            dir=final_path.parent,
            prefix=f".{final_path.stem}-",
            suffix=".tmp",
            delete=False,
        ) as temporary_file:
            temporary_path = Path(temporary_file.name)
        shutil.copy2(validated_pdf, temporary_path)
        if temporary_path.stat().st_size != validated_pdf.stat().st_size:
            raise CvCompilationError("The final PDF copy failed its size check.")
        temporary_path.replace(final_path)
    except CvCompilationError:
        raise
    except OSError as error:
        raise CvCompilationError(f"Unable to publish the final PDF: {error}") from error
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()

    return final_path


def _compile(
    executable: Path,
    source: Path,
    output_dir: Path,
    resource_cache_dir: Path,
    bundle_url: str,
    timeout: int,
) -> tuple[Path, subprocess.CompletedProcess[str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    resource_cache_dir.mkdir(parents=True, exist_ok=True)
    command = [
        str(executable),
        "-X",
        "compile",
        "--bundle",
        bundle_url,
        "--untrusted",
        "--keep-logs",
        "--outdir",
        str(output_dir),
        source.name,
    ]
    environment = os.environ.copy()
    environment["TECTONIC_UNTRUSTED_MODE"] = "1"
    environment["TECTONIC_CACHE_DIR"] = str(resource_cache_dir)
    _configure_fontconfig(environment, resource_cache_dir)
    try:
        completed = subprocess.run(
            command,
            cwd=source.parent,
            env=environment,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as error:
        raise CvCompilationError(
            f"Tectonic exceeded the {timeout}-second compilation timeout."
        ) from error
    except OSError as error:
        raise CvCompilationError(f"Unable to start Tectonic: {error}") from error

    if completed.returncode != 0:
        details = "\n".join(
            part.strip()
            for part in (completed.stdout, completed.stderr)
            if part.strip()
        )
        raise CvCompilationError(
            f"Tectonic failed with exit code {completed.returncode}:\n{details}"
        )
    return output_dir / source.with_suffix(".pdf").name, completed


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Compile a LaTeX CV with a verified Tectonic binary and validate "
            "the generated PDF text."
        )
    )
    parser.add_argument("source", type=Path, help="Path to the main .tex file")
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Build directory (default: <source-dir>/build/<source-name>)",
    )
    parser.add_argument(
        "--final-pdf",
        type=Path,
        help="Published PDF path (default: beside the source .tex)",
    )
    parser.add_argument(
        "--overwrite-final",
        action="store_true",
        help="Replace an existing final PDF instead of choosing a numbered suffix",
    )
    parser.add_argument(
        "--install-tectonic",
        action="store_true",
        help="Download the pinned official Tectonic binary when it is missing",
    )
    parser.add_argument(
        "--tectonic",
        type=Path,
        help="Use a specific Tectonic executable",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=_default_cache_dir(),
        help="Directory used to cache the verified Tectonic binary",
    )
    parser.add_argument(
        "--bundle-url",
        default=DEFAULT_BUNDLE_URL,
        help="Pinned Tectonic TeX resource bundle URL",
    )
    parser.add_argument(
        "--expected-keyword",
        action="append",
        default=[],
        help="Require a visible keyword in extracted PDF text (repeatable)",
    )
    parser.add_argument(
        "--forbidden-keyword",
        action="append",
        default=[],
        help="Reject an unsupported keyword in extracted PDF text (repeatable)",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=240,
        help="Compilation timeout in seconds (default: 240)",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    source = arguments.source.expanduser().resolve()
    cache_dir = arguments.cache_dir.expanduser().resolve()
    output_dir = (
        arguments.output_dir.expanduser().resolve()
        if arguments.output_dir
        else source.parent / "build" / source.stem
    )
    requested_final_pdf = (
        arguments.final_pdf.expanduser().resolve()
        if arguments.final_pdf
        else source.with_suffix(".pdf")
    )
    try:
        _validate_source(source)
        executable = _find_tectonic(arguments.tectonic, cache_dir)
        installed = False
        if executable is None:
            if not arguments.install_tectonic:
                raise CvCompilationError(
                    "Tectonic is not available. Rerun with --install-tectonic "
                    "after obtaining permission to download the pinned official binary."
                )
            executable = _install_tectonic(cache_dir)
            installed = True

        compiler_version = _probe_compiler(executable)
        pdf_path, completed = _compile(
            executable,
            source,
            output_dir,
            cache_dir / "resources",
            arguments.bundle_url,
            arguments.timeout,
        )
        report = _verify_pdf(
            pdf_path,
            arguments.expected_keyword,
            arguments.forbidden_keyword,
        )
        final_pdf = _publish_pdf(
            report.path,
            requested_final_pdf,
            overwrite=arguments.overwrite_final,
        )
    except CvCompilationError as error:
        print(json.dumps({"status": "error", "message": str(error)}, indent=2))
        return 1

    print(
        json.dumps(
            {
                "status": "ok",
                "compiler": str(executable),
                "compiler_version": compiler_version,
                "installed": installed,
                "bundle_url": arguments.bundle_url,
                "source": str(source),
                "build_pdf": str(report.path),
                "pdf": str(final_pdf),
                "published_after_validation": True,
                "pages": report.pages,
                "extracted_characters": report.extracted_characters,
                "verified_keywords": list(report.expected_keywords),
                "compiler_warnings": completed.stderr.strip(),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
