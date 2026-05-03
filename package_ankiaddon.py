"""Build a safe .ankiaddon package for PomodoroVN.

Run from the add-on root:
    python package_ankiaddon.py
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from datetime import datetime
from pathlib import Path, PurePosixPath


DEFAULT_PACKAGE_NAME = "PomoVN"
DEFAULT_OUTPUT_DIR = "ankiaddon_dist"

INCLUDE_ROOT_FILES = {
    "__init__.py",
    "config.json",
}

INCLUDE_DIRS = {
    "assets",
    "pomodoro_qt",
    "web",
}

EXCLUDED_DIR_NAMES = {
    ".git",
    ".idea",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".vscode",
    "__pycache__",
    "build",
    "dist",
    DEFAULT_OUTPUT_DIR,
}

EXCLUDED_FILE_SUFFIXES = {
    ".bak",
    ".db",
    ".log",
    ".pyc",
    ".pyo",
    ".sqlite",
    ".sqlite3",
    ".tmp",
}

EXCLUDED_FILE_NAMES = {
    ".DS_Store",
    "meta.json",
    "package_ankiaddon.py",
    "pomodoro_qt.db",
    "pomodoro_qt.log",
    "pomodoro_qt_state.json",
    "Thumbs.db",
}

RUNTIME_NAME_FRAGMENTS = (
    "cache",
    "history",
    "runtime",
    "state",
)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    src = Path(args.src).expanduser().resolve()
    package_name = sanitize_package_name(args.name)
    out_dir = resolve_output_dir(src, args.out_dir)
    output = out_dir / f"{package_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.ankiaddon"

    validate_source(src)
    files = collect_package_files(src)
    validate_archive_members(files)

    out_dir.mkdir(parents=True, exist_ok=True)
    if output.exists() and not args.overwrite:
        raise SystemExit(f"Output already exists, pass --overwrite to replace: {output}")

    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path, arcname in files:
            archive.write(path, arcname)

    inspect_written_archive(output)
    print_summary(src, output, files)
    return 0


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Package this Anki add-on as a .ankiaddon zip.")
    parser.add_argument("--src", default=".", help="Add-on source root. Defaults to current directory.")
    parser.add_argument("--name", default=DEFAULT_PACKAGE_NAME, help="Output package name prefix.")
    parser.add_argument(
        "--out-dir",
        default=None,
        help=f"Output directory. Defaults to ../{DEFAULT_OUTPUT_DIR} relative to --src.",
    )
    parser.add_argument("--overwrite", action="store_true", help="Allow replacing an existing output file.")
    return parser.parse_args(argv)


def resolve_output_dir(src: Path, out_dir: str | None) -> Path:
    if out_dir:
        return Path(out_dir).expanduser().resolve()
    return (src.parent / DEFAULT_OUTPUT_DIR).resolve()


def sanitize_package_name(name: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in {"-", "_"} else "_" for char in str(name).strip())
    return cleaned or DEFAULT_PACKAGE_NAME


def validate_source(src: Path) -> None:
    if not src.exists() or not src.is_dir():
        raise SystemExit(f"Source folder does not exist or is not a directory: {src}")
    if not (src / "__init__.py").is_file():
        raise SystemExit(f"Missing required root __init__.py: {src / '__init__.py'}")
    for dirname in INCLUDE_DIRS:
        if not (src / dirname).is_dir():
            raise SystemExit(f"Missing required package directory: {src / dirname}")


def collect_package_files(src: Path) -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = []

    for name in sorted(INCLUDE_ROOT_FILES):
        path = src / name
        if path.is_file() and not should_exclude(path, src):
            files.append((path, to_arcname(path, src)))

    for dirname in sorted(INCLUDE_DIRS):
        root = src / dirname
        for path in sorted(root.rglob("*")):
            if path.is_file() and not should_exclude(path, src):
                files.append((path, to_arcname(path, src)))

    if not files:
        raise SystemExit("No files collected for packaging.")
    return files


def should_exclude(path: Path, src: Path) -> bool:
    rel = path.relative_to(src)
    parts = set(rel.parts)
    if parts & EXCLUDED_DIR_NAMES:
        return True
    if path.name in EXCLUDED_FILE_NAMES:
        return True
    if path.suffix.lower() in EXCLUDED_FILE_SUFFIXES:
        return True
    lower_name = path.name.lower()
    if lower_name.endswith(".ankiaddon"):
        return True
    if is_runtime_data_candidate(rel):
        return True
    return False


def is_runtime_data_candidate(rel: Path) -> bool:
    lower = rel.as_posix().lower()
    if lower in {"config.json", "__init__.py"}:
        return False
    if lower.startswith(("assets/", "pomodoro_qt/locales/", "web/")):
        return False
    if lower.endswith((".py", ".json", ".html", ".css", ".js", ".svg")):
        return False
    return any(fragment in lower for fragment in RUNTIME_NAME_FRAGMENTS)


def to_arcname(path: Path, src: Path) -> str:
    return PurePosixPath(path.relative_to(src).as_posix()).as_posix()


def validate_archive_members(files: list[tuple[Path, str]]) -> None:
    arcnames = [arcname for _path, arcname in files]
    if "__init__.py" not in arcnames:
        raise SystemExit("Package would not contain root __init__.py.")

    for arcname in arcnames:
        parts = PurePosixPath(arcname).parts
        if len(parts) >= 2 and parts[0].lower() in {"pomodoro", "pomodovn"} and parts[1] == "__init__.py":
            raise SystemExit(f"Package contains a wrapped root folder: {arcname}")
        if "__pycache__" in parts or arcname.endswith(".pyc"):
            raise SystemExit(f"Package contains Python cache output: {arcname}")
        if Path(arcname).suffix.lower() in {".db", ".sqlite", ".sqlite3", ".log", ".tmp", ".bak"}:
            raise SystemExit(f"Package contains runtime or temporary data: {arcname}")
        if PurePosixPath(arcname).name in {"pomodoro_qt_state.json", "pomodoro_qt.db", "meta.json"}:
            raise SystemExit(f"Package contains user/runtime data: {arcname}")


def inspect_written_archive(output: Path) -> None:
    with zipfile.ZipFile(output) as archive:
        names = archive.namelist()
    validate_archive_members([(Path(name), name) for name in names])


def print_summary(src: Path, output: Path, files: list[tuple[Path, str]]) -> None:
    print(f"Source folder: {src}")
    print(f"Output file: {output}")
    print(f"Files packaged: {len(files)}")
    print("Sample package files:")
    for _path, arcname in files[:20]:
        print(f"  {arcname}")


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        raise SystemExit(130)
