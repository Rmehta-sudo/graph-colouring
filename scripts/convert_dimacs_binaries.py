#!/usr/bin/env python3
"""Convert DIMACS .col.b binaries to ASCII .col files using bin2asc.o."""

from __future__ import annotations

import subprocess
from pathlib import Path


def move_col_b_files(dataset_dir: Path, col_b_dir: Path) -> list[Path]:
    """Move all .col.b files into the archive directory and return their new paths."""
    col_b_dir.mkdir(parents=True, exist_ok=True)
    moved: list[Path] = []
    for source in dataset_dir.glob("*.col.b"):
        destination = col_b_dir / source.name
        if destination.exists():
            # Skip if already archived.
            continue
        source.rename(destination)
        moved.append(destination)
    return moved


def convert_files(bin_path: Path, files: list[Path], working_dir: Path) -> None:
    """Run bin2asc.o over each archived file, writing .col outputs into working_dir."""
    if not bin_path.exists():
        raise FileNotFoundError(f"bin2asc executable not found at {bin_path}")
    for file_path in files:
        rel_path = file_path.relative_to(working_dir)
        subprocess.run([str(bin_path), str(rel_path)], cwd=working_dir, check=True)


def main() -> None:
    """Archive .col.b files and convert them to ASCII .col format."""
    scripts_dir = Path(__file__).resolve().parent
    dataset_dir = scripts_dir / "datasets" / "dimacs"
    col_b_dir = dataset_dir / "col-b"
    bin2asc = dataset_dir / "bin2asc.o"

    moved_files = move_col_b_files(dataset_dir, col_b_dir)
    if not moved_files:
        # Even if nothing moved, attempt conversion of any existing archived files.
        moved_files = list(col_b_dir.glob("*.col.b"))
    if not moved_files:
        print("No .col.b files found for conversion.")
        return

    convert_files(bin2asc, moved_files, dataset_dir)
    print(f"Converted {len(moved_files)} file(s) into {dataset_dir}")


if __name__ == "__main__":
    main()
