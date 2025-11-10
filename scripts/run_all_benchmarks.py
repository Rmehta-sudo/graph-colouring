#!/usr/bin/env python3
"""
Run all algorithms (welsh_powell, dsatur, simulated_annealing, genetic, exact_solver)
over a set of DIMACS graphs with timeout and retry, aggregating results into a single CSV.

Policy:
- First pass: timeout 15s per (graph, algo). If timeout -> defer.
- Second pass: retry deferred with timeout 30s. If timeout again -> record status "timeout>45s".
- On non-zero exit (other errors) -> record status "error".

Output: results/run_all_results.csv with schema:
algorithm,graph_name,vertices,edges,colors_used,known_optimal,runtime_ms,status

Notes:
- Uses build/benchmark_runner. Ensure the binary exists (make all) before running.
- Graphs are discovered under scripts/datasets/dimacs/*.col by default.
- You can optionally include generated graphs via --include-generated.
"""
from __future__ import annotations

import argparse
import csv
import os
import math
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "build" / "benchmark_runner"
DIMACS_DIR = ROOT / "scripts" / "datasets" / "dimacs"
GENERATED_DIR = ROOT / "scripts" / "datasets" / "generated"
RESULTS_DIR = ROOT / "results"
AGGREGATE_CSV = RESULTS_DIR / "run_all_results.csv"
TMP_RESULT = RESULTS_DIR / "tmp_run.csv"
RAW_DIR = RESULTS_DIR / "raw"

ALGORITHMS = [
    "welsh_powell",
    "dsatur",
    "simulated_annealing",
    "genetic",
    "exact_solver",
]

HEADER = [
    "algorithm",
    "graph_name",
    "vertices",
    "edges",
    "colors_used",
    "known_optimal",
    "runtime_ms",
    "status",
]

METADATA_DIMACS = ROOT / "scripts" / "datasets" / "metadata-dimacs.csv"
METADATA_GENERATED = ROOT / "scripts" / "datasets" / "metadata-generated.csv"

def load_known_optimal() -> dict[str, int]:
    mapping: dict[str, int] = {}
    for meta in (METADATA_DIMACS, METADATA_GENERATED):
        if not meta.exists():
            continue
        try:
            with meta.open("r", encoding="utf-8", newline="") as fh:
                reader = csv.DictReader(fh)
                for row in reader:
                    name = row.get("graph_name", "").strip()
                    ko = row.get("known_optimal", "").strip()
                    if name and ko:
                        try:
                            mapping[name] = int(ko)
                        except Exception:
                            pass
        except Exception:
            continue
    return mapping


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--include-generated",
        action="store_true",
        help="Also include scripts/datasets/generated/*.col",
    )
    p.add_argument(
        "--graphs",
        nargs="*",
        help="Explicit list of graph .col paths (overrides directory scan)",
    )
    p.add_argument(
        "--first-timeout",
        type=float,
        default=15.0,
        help="Seconds for first-pass timeout per job (default: 15)",
    )
    p.add_argument(
        "--second-timeout",
        type=float,
        default=30.0,
        help="Seconds for retry timeout per job (default: 30)",
    )
    return p.parse_args()


def ensure_dirs() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)


def discover_graphs(include_generated: bool, explicit: List[str] | None) -> List[Path]:
    if explicit:
        return [Path(p) if Path(p).is_absolute() else ROOT / p for p in explicit]
    graphs = sorted(DIMACS_DIR.glob("*.col"))
    if include_generated:
        graphs += sorted(GENERATED_DIR.glob("*.col"))
    return graphs


def read_dimacs_header(path: Path) -> Tuple[int, int]:
    # Return (V, E) from p-line; if missing, best-effort parse
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line:
                    continue
                c = line[0]
                if c in ("c", "%", "#"):
                    continue
                if c == "p":
                    parts = line.strip().split()
                    if len(parts) >= 4 and parts[1] == "edge":
                        return int(parts[2]), int(parts[3])
    except Exception:
        pass
    # Fallback: count vertices by scanning edges
    V = 0
    E = 0
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if line and line[0] == "e":
                    try:
                        _, u, v = line.strip().split()
                        u = int(u)
                        v = int(v)
                        V = max(V, u, v)
                        E += 1
                    except Exception:
                        continue
    except Exception:
        pass
    return V, E


def append_row(row: List[str]) -> None:
    new_file = not AGGREGATE_CSV.exists() or AGGREGATE_CSV.stat().st_size == 0
    with AGGREGATE_CSV.open("a", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        if new_file:
            w.writerow(HEADER)
        w.writerow(row)


def parse_tmp_result() -> Tuple[str, str, str, str, str, str, str]:
    # Returns tuple of 7 fields matching first 7 columns, else raises
    with TMP_RESULT.open("r", encoding="utf-8", newline="") as fh:
        r = csv.DictReader(fh)
        last = None
        for last in r:
            pass
        if not last:
            raise RuntimeError("Empty tmp results")
        return (
            last.get("algorithm", ""),
            last.get("graph_name", ""),
            last.get("vertices", ""),
            last.get("edges", ""),
            last.get("colors_used", ""),
            last.get("known_optimal", ""),
            last.get("runtime_ms", ""),
        )


def run_one(graph_path: Path, algo: str, timeout_s: float) -> Tuple[bool, str]:
    graph_name = graph_path.stem
    output_path = RAW_DIR / f"{graph_name}_{algo}.col"
    # Use a temporary results file to capture a single row for aggregation
    if TMP_RESULT.exists():
        TMP_RESULT.unlink(missing_ok=True)  # type: ignore[arg-type]
    cmd = [
        str(BENCH),
        "--algorithm", algo,
        "--input", str(graph_path),
        "--output", str(output_path),
        "--results", str(TMP_RESULT),
        "--graph-name", graph_name,
    ]
    try:
        cp = subprocess.run(cmd, cwd=ROOT, timeout=timeout_s, capture_output=True, text=True)
    except subprocess.TimeoutExpired:
        return False, "timeout"
    if cp.returncode != 0:
        # Keep stdout/stderr for debugging, but just mark as error in CSV
        return False, "error"
    return True, "ok"


def main() -> int:
    args = parse_args()
    ensure_dirs()

    if not BENCH.exists():
        print("Error: build/benchmark_runner not found. Run 'make all' first.", file=sys.stderr)
        return 2

    graphs = discover_graphs(args.include_generated, args.graphs)
    if not graphs:
        print("No graphs found to run.")
        return 0

    known_map = load_known_optimal()

    deferred: List[Tuple[Path, str]] = []

    # First pass
    for algo in ALGORITHMS:
        for g in graphs:
            V, E = read_dimacs_header(g)
            name = g.stem
            ok, reason = run_one(g, algo, args.first_timeout)
            if ok:
                try:
                    a, gn, v, e, c, k, t = parse_tmp_result()
                    # Fill known_optimal if missing
                    if (not k) or k == "0":
                        meta_key_with = gn if gn.endswith('.col') else gn + '.col'
                        meta_key_plain = gn
                        ko = None
                        if meta_key_with in known_map:
                            ko = known_map[meta_key_with]
                        elif meta_key_plain in known_map:
                            ko = known_map[meta_key_plain]
                        if ko is not None:
                            k = str(ko)
                    append_row([a, gn, v, e, c, k, t, "ok"])
                except Exception:
                    meta_key_with = name + '.col'
                    ko = known_map.get(meta_key_with) or known_map.get(name)
                    append_row([algo, name, str(V), str(E), "", str(ko) if ko else "", "", "ok(no-parse)"])
            else:
                if reason == "timeout":
                    deferred.append((g, algo))
                else:
                    meta_key_with = name + '.col'
                    ko = known_map.get(meta_key_with) or known_map.get(name)
                    append_row([algo, name, str(V), str(E), "", str(ko) if ko else "", "", "error"]) 

    # Second pass (retry timeouts)
    for g, algo in deferred:
        V, E = read_dimacs_header(g)
        name = g.stem
        ok, reason = run_one(g, algo, args.second_timeout)
        if ok:
            try:
                a, gn, v, e, c, k, t = parse_tmp_result()
                if (not k) or k == "0":
                    meta_key_with = gn if gn.endswith('.col') else gn + '.col'
                    meta_key_plain = gn
                    ko = None
                    if meta_key_with in known_map:
                        ko = known_map[meta_key_with]
                    elif meta_key_plain in known_map:
                        ko = known_map[meta_key_plain]
                    if ko is not None:
                        k = str(ko)
                append_row([a, gn, v, e, c, k, t, "ok(retry)"])
            except Exception:
                meta_key_with = name + '.col'
                ko = known_map.get(meta_key_with) or known_map.get(name)
                append_row([algo, name, str(V), str(E), "", str(ko) if ko else "", "", "ok(retry,no-parse)"])
        else:
            meta_key_with = name + '.col'
            ko = known_map.get(meta_key_with) or known_map.get(name)
            append_row([algo, name, str(V), str(E), "", str(ko) if ko else "", "", "timeout>45s"]) 

    print(f"Aggregate written to {AGGREGATE_CSV}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
