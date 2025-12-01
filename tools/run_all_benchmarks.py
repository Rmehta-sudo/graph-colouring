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
DIMACS_DIR = ROOT / "data" / "dimacs"
GENERATED_DIR = ROOT / "data" / "generated"
RESULTS_DIR = ROOT / "results"
AGGREGATE_CSV = RESULTS_DIR / "run_all_results.csv"
TMP_RESULT = RESULTS_DIR / "tmp_run.csv"
colourings_DIR = RESULTS_DIR / "colourings"

# Order: fast heuristics first, then metaheuristics, exact solver last
ALGORITHMS = [
    "dsatur",
    "welsh_powell",
    "simulated_annealing",
    "tabu_search",
    "genetic",
]

# Exact solver handled separately with its own timeout
EXACT_SOLVER = "exact_solver"

# Default timeouts per algorithm (can be overridden via CLI)
DEFAULT_TIMEOUTS = {
    "dsatur": 60.0,
    "welsh_powell": 60.0,
    "simulated_annealing": 120.0,
    "tabu_search": 120.0,
    "genetic": 180.0,
    "exact_solver": 300.0,
}

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
        default=150.0,
        help="Default first-pass timeout per job in seconds (default: 150)",
    )
    p.add_argument(
        "--second-timeout",
        type=float,
        default=300.0,
        help="Default retry timeout per job in seconds (default: 300)",
    )
    p.add_argument(
        "--no-exact",
        action="store_true",
        help="Skip exact_solver algorithm entirely",
    )
    p.add_argument(
        "--exact-timeout",
        type=float,
        default=300.0,
        help="Timeout for exact_solver in seconds (default: 300)",
    )
    p.add_argument(
        "--exact-max-vertices",
        type=int,
        default=500,
        help="Max vertices for exact_solver (skip larger graphs, default: 500)",
    )
    p.add_argument(
        "--algo-timeout",
        action="append",
        nargs=2,
        metavar=("ALGO", "SECONDS"),
        help="Set timeout for a specific algorithm, e.g. --algo-timeout genetic 240",
    )
    p.add_argument(
        "--output-file",
        "-o",
        type=str,
        default=None,
        help="Custom output CSV filename (default: run_all_results.csv). Use e.g. 'dimacs_results.csv' or 'generated_results.csv'",
    )
    return p.parse_args()


def ensure_dirs() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    colourings_DIR.mkdir(parents=True, exist_ok=True)


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


def append_row(row: List[str], output_csv: Path) -> None:
    new_file = not output_csv.exists() or output_csv.stat().st_size == 0
    with output_csv.open("a", encoding="utf-8", newline="") as fh:
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
    output_path = colourings_DIR / f"{graph_name}_{algo}.col"
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

    # Determine output CSV file
    if args.output_file:
        output_csv = RESULTS_DIR / args.output_file
    else:
        output_csv = AGGREGATE_CSV
    
    print(f"Results will be written to: {output_csv}")

    # Build per-algorithm timeout map
    algo_timeouts = dict(DEFAULT_TIMEOUTS)
    if args.algo_timeout:
        for algo_name, timeout_str in args.algo_timeout:
            algo_timeouts[algo_name] = float(timeout_str)

    deferred: List[Tuple[Path, str]] = []

    # Run algorithm-by-algorithm (all graphs for one algo, then next algo)
    # Order: dsatur, welsh_powell, simulated_annealing, tabu_search, genetic
    for algo in ALGORITHMS:
        timeout_first = algo_timeouts.get(algo, args.first_timeout)
        timeout_second = algo_timeouts.get(algo, args.second_timeout)
        print(f"\n{'='*60}")
        print(f"Running {algo} on all graphs (timeout: {timeout_first}s)")
        print(f"{'='*60}")
        
        for g in graphs:
            V, E = read_dimacs_header(g)
            name = g.stem
            ok, reason = run_one(g, algo, timeout_first)
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
                    append_row([a, gn, v, e, c, k, t, "ok"], output_csv)
                    print(f"  ✓ {name}: {c} colors in {t}ms")
                except Exception:
                    meta_key_with = name + '.col'
                    ko = known_map.get(meta_key_with) or known_map.get(name)
                    append_row([algo, name, str(V), str(E), "", str(ko) if ko else "", "", "ok(no-parse)"], output_csv)
                    print(f"  ✓ {name}: completed (no parse)")
            else:
                meta_key_with = name + '.col'
                ko = known_map.get(meta_key_with) or known_map.get(name)
                if reason == "timeout":
                    print(f"  ⏱ {name}: timeout (first pass)")
                    append_row([algo, name, str(V), str(E), "", str(ko) if ko else "", "", "timeout(first-pass)"], output_csv)
                    deferred.append((g, algo))
                else:
                    print(f"  ✗ {name}: error")
                    append_row([algo, name, str(V), str(E), "", str(ko) if ko else "", "", "error"], output_csv) 

    # Second pass (retry timeouts) - grouped by algorithm
    if deferred:
        print(f"\n{'='*60}")
        print(f"Retrying {len(deferred)} timed-out jobs...")
        print(f"{'='*60}")
        
        for g, algo in deferred:
            timeout_second = algo_timeouts.get(algo, args.second_timeout)
            V, E = read_dimacs_header(g)
            name = g.stem
            ok, reason = run_one(g, algo, timeout_second)
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
                    append_row([a, gn, v, e, c, k, t, "ok(retry)"], output_csv)
                    print(f"  ✓ {name}/{algo}: {c} colors in {t}ms (retry)")
                except Exception:
                    meta_key_with = name + '.col'
                    ko = known_map.get(meta_key_with) or known_map.get(name)
                    append_row([algo, name, str(V), str(E), "", str(ko) if ko else "", "", "ok(retry,no-parse)"], output_csv)
                    print(f"  ✓ {name}/{algo}: completed (retry, no parse)")
            else:
                meta_key_with = name + '.col'
                ko = known_map.get(meta_key_with) or known_map.get(name)
                append_row([algo, name, str(V), str(E), "", str(ko) if ko else "", "", "timeout>retry"], output_csv)
                print(f"  ✗ {name}/{algo}: timeout after retry")

    # Run exact_solver last (only if --no-exact is not set)
    if not args.no_exact:
        print(f"\n{'='*60}")
        print(f"Running {EXACT_SOLVER} on eligible graphs (timeout: {args.exact_timeout}s, max vertices: {args.exact_max_vertices})")
        print(f"{'='*60}")
        
        for g in graphs:
            V, E = read_dimacs_header(g)
            name = g.stem
            
            # Skip graphs that are too large for exact solver
            if V > args.exact_max_vertices:
                print(f"  ⊘ {name}: skipped (V={V} > {args.exact_max_vertices})")
                meta_key_with = name + '.col'
                ko = known_map.get(meta_key_with) or known_map.get(name)
                append_row([EXACT_SOLVER, name, str(V), str(E), "", str(ko) if ko else "", "", "skipped(too-large)"], output_csv)
                continue
            
            ok, reason = run_one(g, EXACT_SOLVER, args.exact_timeout)
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
                    append_row([a, gn, v, e, c, k, t, "ok"], output_csv)
                    print(f"  ✓ {name}: {c} colors in {t}ms")
                except Exception:
                    meta_key_with = name + '.col'
                    ko = known_map.get(meta_key_with) or known_map.get(name)
                    append_row([EXACT_SOLVER, name, str(V), str(E), "", str(ko) if ko else "", "", "ok(no-parse)"], output_csv)
                    print(f"  ✓ {name}: completed (no parse)")
            else:
                meta_key_with = name + '.col'
                ko = known_map.get(meta_key_with) or known_map.get(name)
                if reason == "timeout":
                    print(f"  ⏱ {name}: timeout ({args.exact_timeout}s)")
                    append_row([EXACT_SOLVER, name, str(V), str(E), "", str(ko) if ko else "", "", "timeout"], output_csv)
                else:
                    print(f"  ✗ {name}: error")
                    append_row([EXACT_SOLVER, name, str(V), str(E), "", str(ko) if ko else "", "", "error"], output_csv)

    print(f"\n{'='*60}")
    print(f"Aggregate written to {output_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
