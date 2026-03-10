from __future__ import annotations

import argparse
import shutil
from pathlib import Path

EPHE_EXTENSIONS = {".se1", ".se2", ".sef"}
SKIP_DIR_NAMES = {".git", ".venv", "__pycache__", ".pytest_cache"}


def find_ephemeris_files(repo_root: Path, dest_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in repo_root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in EPHE_EXTENSIONS:
            continue
        if any(part in SKIP_DIR_NAMES for part in path.parts):
            continue
        if dest_dir in path.parents:
            continue
        files.append(path)
    return sorted(files)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect Swiss Ephemeris files into data/ephe")
    parser.add_argument("--copy", action="store_true", help="copy instead of move")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    dest_dir = repo_root / "data" / "ephe"
    dest_dir.mkdir(parents=True, exist_ok=True)

    candidates = find_ephemeris_files(repo_root, dest_dir)
    if not candidates:
        print("[INFO] No ephemeris files found outside data/ephe.")
        return

    operation = shutil.copy2 if args.copy else shutil.move
    op_name = "COPY" if args.copy else "MOVE"

    for src in candidates:
        dst = dest_dir / src.name
        if dst.exists():
            print(f"[SKIP] {src} -> {dst} (already exists)")
            continue
        operation(str(src), str(dst))
        print(f"[{op_name}] {src} -> {dst}")

    print("\n[OK] ephemeris files organized.")
    print(f"ASTROLOGY_EPHE_PATH={dest_dir}")


if __name__ == "__main__":
    main()
