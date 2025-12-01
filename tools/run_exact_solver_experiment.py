#!/usr/bin/env python3
"""
Run exact_solver algorithm over DIMACS and generated graphs with a 3-stage timeout strategy.

Strategy:
1. Run all graphs with 30s timeout.
2. Retry timed-out graphs with 60s timeout.
3. Retry timed-out graphs again with 120s timeout.
4. Record all results (including final timeouts) to results/exact_solver_experiment.csv.
"""
import csv
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Tuple, Set

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "build" / "benchmark_runner"
DIMACS_DIR = ROOT / "data" / "dimacs"
GENERATED_DIR = ROOT / "data" / "generated"
RESULTS_DIR = ROOT / "results"
OUTPUT_CSV = RESULTS_DIR / "exact_solver_experiment.csv"
TMP_RESULT = RESULTS_DIR / "tmp_exact_run.csv"
COLOURINGS_DIR = RESULTS_DIR / "colourings"

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

TIMEOUT_STAGES = [30.0, 60.0, 120.0]

def ensure_dirs() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    COLOURINGS_DIR.mkdir(parents=True, exist_ok=True)

def discover_graphs(directory: Path) -> List[Path]:
    return sorted(directory.glob("*.col"))

def read_graph_metadata(path: Path) -> Tuple[int, int]:
    """Read V and E from graph file header."""
    V = 0
    E = 0
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                if not line: continue
                if line.startswith("p edge"):
                    parts = line.strip().split()
                    if len(parts) >= 4:
                        return int(parts[2]), int(parts[3])
                elif line.startswith("e "):
                    E += 1
                    parts = line.strip().split()
                    if len(parts) >= 3:
                        V = max(V, int(parts[1]), int(parts[2]))
    except Exception:
        pass
    return V, E

def append_row(row: List[str]) -> None:
    new_file = not OUTPUT_CSV.exists() or OUTPUT_CSV.stat().st_size == 0
    with OUTPUT_CSV.open("a", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        if new_file:
            w.writerow(HEADER)
        w.writerow(row)

def parse_tmp_result() -> Tuple[str, str, str, str, str, str, str]:
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

def run_one(graph_path: Path, timeout_s: float) -> Tuple[bool, str]:
    graph_name = graph_path.stem
    output_path = COLOURINGS_DIR / f"{graph_name}_exact.col"
    
    if TMP_RESULT.exists():
        TMP_RESULT.unlink()

    cmd = [
        str(BENCH),
        "--algorithm", "exact_solver",
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
        return False, "error"
    
    return True, "ok"

def run_batch(graphs: List[Path], dataset_name: str) -> None:
    print(f"\n{'='*60}")
    print(f"Starting batch: {dataset_name} ({len(graphs)} graphs)")
    print(f"{'='*60}")

    remaining_graphs = graphs[:]
    
    for stage_idx, timeout in enumerate(TIMEOUT_STAGES):
        if not remaining_graphs:
            break
            
        print(f"\n--- Stage {stage_idx + 1}/{len(TIMEOUT_STAGES)}: Timeout {timeout}s ---")
        next_stage_graphs = []
        
        for g in remaining_graphs:
            name = g.stem
            print(f"Running {name}...", end="", flush=True)
            
            start_t = time.time()
            ok, reason = run_one(g, timeout)
            elapsed = time.time() - start_t
            
            if ok:
                try:
                    # Parse result and save
                    _, gn, v, e, c, k, t = parse_tmp_result()
                    append_row(["exact_solver", gn, v, e, c, k, t, "ok"])
                    print(f" \r  ✓ {name}: {c} colors in {t}ms")
                except Exception as e:
                    print(f" \r  ✓ {name}: completed (parse error)")
                    V, E = read_graph_metadata(g)
                    append_row(["exact_solver", name, str(V), str(E), "", "", "", "ok(no-parse)"])
            else:
                if reason == "timeout":
                    print(f" \r  ⏱ {name}: timeout (> {timeout}s)")
                    # If this is the last stage, record the failure
                    if stage_idx == len(TIMEOUT_STAGES) - 1:
                        V, E = read_graph_metadata(g)
                        append_row(["exact_solver", name, str(V), str(E), "", "", "", f"timeout>{timeout}s"])
                    else:
                        next_stage_graphs.append(g)
                else:
                    print(f" \r  ✗ {name}: error")
                    V, E = read_graph_metadata(g)
                    append_row(["exact_solver", name, str(V), str(E), "", "", "", "error"])
        
        remaining_graphs = next_stage_graphs

def main() -> int:
    ensure_dirs()
    
    if not BENCH.exists():
        print("Error: build/benchmark_runner not found. Run 'make all' first.")
        return 1

    # Phase 1: DIMACS
    dimacs_graphs = discover_graphs(DIMACS_DIR)
    if dimacs_graphs:
        run_batch(dimacs_graphs, "DIMACS")
    else:
        print("No DIMACS graphs found.")

    # Phase 2: Generated
    generated_graphs = discover_graphs(GENERATED_DIR)
    if generated_graphs:
        run_batch(generated_graphs, "Generated")
    else:
        print("No generated graphs found.")

    print(f"\n{'='*60}")
    print(f"Experiment completed. Results in {OUTPUT_CSV}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
