#!/usr/bin/env python3
"""Animate colouring snapshots for a given graph and algorithm.

Supported algorithms (all snapshot-enabled):
    - dsatur
    - welsh_powell
    - genetic
    - simulated_annealing
    - exact_solver

You can either pre-generate snapshots using the C++ runner or let this script
invoke the runner automatically (default). Snapshot file pattern:
    snapshots-colouring/<algo>-<graph>-snnapshots.txt

Basic usage examples:
    python3 scripts/animate_coloring.py --graph myciel6 --algo dsatur
    python3 scripts/animate_coloring.py --graph myciel6 --algo simulated_annealing --interval 0.05
    python3 scripts/animate_coloring.py --graph myciel6 --algo genetic --population-size 128 --generations 800
    python3 scripts/animate_coloring.py --graph myciel6 --algo exact_solver --exact-progress-interval 2.5

Algorithm-specific optional flags when auto-running:
    genetic:
        --population-size            (default 64)
        --generations                (max generations, default 500)
        --mutation-rate              (default 0.02)
    exact_solver:
        --exact-progress-interval    (seconds between progress stderr reports)

The script will:
    1. Resolve the graph path (bare name, relative path under datasets, or absolute path).
    2. Run the C++ benchmark_runner with --save-snapshots unless --skip-run is given.
    3. Load the snapshot file (each line = full colour vector; -1 for uncoloured).
    4. Animate frames with matplotlib, drawing edges. Layout options: spring (needs networkx) or circular.

Colours are mapped to a qualitative palette; -1 appears as light gray.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
import os
from typing import List, Tuple, Dict
import subprocess
import math
from itertools import combinations
import time
try:
    import networkx as nx  # optional, for better layout
except Exception:
    nx = None  # fallback handled

try:
    import matplotlib.pyplot as plt
    import matplotlib.colors as mcolors
except Exception as e:
    # Friendly message for common NumPy/Matplotlib ABI issues
    import sys as _sys
    print("Failed to import matplotlib. This is often due to a NumPy/Matplotlib version mismatch.", file=_sys.stderr)
    print("Hint: Use a consistent environment (e.g., conda) and install compatible versions.", file=_sys.stderr)
    print("  Options:", file=_sys.stderr)
    print("   - conda:  conda install 'matplotlib>=3.9' 'numpy>=2.0'  (same channel)", file=_sys.stderr)
    print("   - or:     conda install 'numpy<2'  (to match older matplotlib)", file=_sys.stderr)
    print("   - pip:    pip install --upgrade 'matplotlib>=3.9'  OR  pip install 'numpy<2'", file=_sys.stderr)
    raise

ROOT = Path(__file__).resolve().parents[1]
SNAP_DIR = ROOT / "snapshots-colouring"
DATASETS_DIR = ROOT / "scripts" / "datasets"
DIMACS_DIR = DATASETS_DIR / "dimacs"
GENERATED_DIR = DATASETS_DIR / "generated"
SIMPLE_TESTS_DIR = DATASETS_DIR / "simple-tests"
NETWORK_REPO_DIR = DATASETS_DIR / "network-repo"
BENCH = ROOT / "build" / "benchmark_runner"

PALETTE = list(mcolors.TABLEAU_COLORS.values()) + [
    '#e6194b','#3cb44b','#ffe119','#4363d8','#f58231','#911eb4','#46f0f0','#f032e6','#bcf60c','#fabebe',
    '#008080','#e6beff','#9a6324','#fffac8','#800000','#aaffc3','#808000','#ffd8b1','#000075','#808080'
]


def print_full_help() -> None:
    msg = """
Snapshot animation helper for 5 algorithms: dsatur, welsh_powell, genetic, simulated_annealing, exact_solver

Basics:
    python3 scripts/animate_coloring.py --graph myciel6 --algo dsatur
    python3 scripts/animate_coloring.py --graph generated/flat300_20_0.col --algo simulated_annealing --interval 0.05
    python3 scripts/animate_coloring.py --graph myciel3 --algo exact_solver --exact-progress-interval 2

Run all algos side-by-side:
    python3 scripts/animate_coloring.py --graph myciel6 --all-algos

Manual stepping (advance on keypress):
    python3 scripts/animate_coloring.py --graph myciel6 --algo genetic --manual
    Keys: enter/space/k/right = next, left/h = back, q/escape = quit

Animation timing:
    --interval X        Seconds between frames for all algorithms (default 0.2)
    --sa-interval X     Override interval for simulated_annealing (has many more iterations)
    Example: python3 scripts/animate_coloring.py --graph myciel6 --algo simulated_annealing --sa-interval 0.01
    Example: python3 scripts/animate_coloring.py --graph myciel6 --all-algos --sa-interval 0.05

Genetic algorithm tuning (applies when --algo genetic):
    --population-size N   (default 64)
    --generations N       (default 500)
    --mutation-rate X     (default 0.02)

Exact solver progress (stderr):
    --exact-progress-interval S   sets env EXACT_PROGRESS_INTERVAL=S

Graph path argument:
    Interpreted relative to scripts/datasets/. Examples:
        dimacs/myciel6.col
        generated/flat300_20_0.col
        simple-tests/tiny.col
    Bare names (e.g., myciel6) will be searched under dimacs/, generated/, and simple-tests/
""".strip()
    print(msg)


def parse_args() -> argparse.Namespace:
    # Check for --full-help before argparse validation
    if "--full-help" in sys.argv:
        print_full_help()
        sys.exit(0)
    
    # Check if --all-algos is present to make --algo optional
    all_algos_mode = "--all-algos" in sys.argv
    
    p = argparse.ArgumentParser(description="Run C++ colouring (producing snapshots) and animate with graph edges.")
    p.add_argument(
        "--graph",
        required=True,
        help=(
            "Graph id: bare name (myciel6) or path relative to scripts/datasets (e.g. dimacs/myciel6.col, generated/flat300_20_0.col) or absolute path."
        ),
    )
    p.add_argument("--algo", required=not all_algos_mode, choices=["dsatur", "welsh_powell", "genetic", "simulated_annealing", "exact_solver"], help="Snapshot-enabled algorithm (not required with --all-algos)")
    p.add_argument("--interval", type=float, default=0.2, help="Seconds between frames (default 0.2)")
    p.add_argument("--sa-interval", type=float, help="Override interval specifically for simulated_annealing (has many more iterations)")
    p.add_argument("--manual", action="store_true", help="Manual stepping mode: next (enter/space/k/right), back (left/h), quit (q/escape).")
    p.add_argument("--repeat", action="store_true", help="Loop animation indefinitely")
    p.add_argument("--layout", choices=["spring", "circular"], default="spring", help="Layout strategy (default spring; circular fallback)")
    p.add_argument("--seed", type=int, default=42, help="Random seed for layout (spring)")
    p.add_argument("--skip-run", action="store_true", help="Assume snapshots already exist; don't invoke C++ binary")
    p.add_argument("--all-algos", action="store_true", help="Animate all 5 algorithms side-by-side for the given graph")
    p.add_argument("--full-help", action="store_true", help="Print extended usage, examples, and GA/Exact settings, then exit")
    # Genetic algorithm tuning
    p.add_argument("--population-size", type=int, default=64, help="Genetic: population size (default 64)")
    p.add_argument("--generations", type=int, default=500, help="Genetic: max generations (default 500)")
    p.add_argument("--mutation-rate", type=float, default=0.02, help="Genetic: mutation rate (default 0.02)")
    # Exact solver progress interval
    p.add_argument("--exact-progress-interval", type=float, help="Exact solver: set EXACT_PROGRESS_INTERVAL (seconds)")
    args = p.parse_args()
    if args.all_algos and args.algo:
        # If --all-algos is set we ignore --algo (can still be provided)
        pass
    return args


def resolve_graph_path_and_name(arg: str) -> tuple[Path, str]:
    p = Path(arg)
    # Absolute path
    if p.is_absolute():
        if p.exists():
            return p, p.stem
        if p.suffix != ".col":
            q = p.with_suffix(".col")
            if q.exists():
                return q, q.stem
        raise FileNotFoundError(f"Graph file not found: {p}")
    # Relative under datasets
    rel = DATASETS_DIR / p
    if p.parent != Path('.'):
        if rel.exists():
            return rel, rel.stem
        if rel.suffix != ".col":
            rel_col = rel.with_suffix(".col")
            if rel_col.exists():
                return rel_col, rel_col.stem
        raise FileNotFoundError(f"Graph not found under scripts/datasets/: {arg}")
    # Bare name
    name = p.stem if p.suffix == ".col" else str(p)
    for c in (
        DIMACS_DIR / f"{name}.col",
        GENERATED_DIR / f"{name}.col",
        SIMPLE_TESTS_DIR / f"{name}.col",
        NETWORK_REPO_DIR / f"{name}.col",
    ):
        if c.exists():
            return c, c.stem
    raise FileNotFoundError(f"Graph '{arg}' not found under datasets (searched dimacs/, generated/, simple-tests/, network-repo/)")


def read_graph(path: Path) -> Tuple[int, List[Tuple[int,int]]]:
    """Return (vertex_count, edges) with 0-based vertices."""
    v_count = 0
    edges: List[Tuple[int,int]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if not line or line[0] in ('c','%','#'):
                continue
            if line.startswith('p '):
                parts = line.strip().split()
                if len(parts) >= 4 and parts[1] == 'edge':
                    try:
                        v_count = int(parts[2])
                    except Exception:
                        pass
            elif line.startswith('e '):
                parts = line.strip().split()
                if len(parts) >= 3:
                    try:
                        u = int(parts[1]) - 1
                        v = int(parts[2]) - 1
                        if u != v:
                            edges.append((u,v))
                            v_count = max(v_count, u+1, v+1)
                    except Exception:
                        continue
    return v_count, edges


def load_snapshots(algo: str, graph_name: str) -> List[List[int]]:
    snap_path = SNAP_DIR / f"{algo}-{graph_name}-snnapshots.txt"
    if not snap_path.exists():
        raise FileNotFoundError(f"Snapshots file not found: {snap_path}. Run benchmark_runner with --save-snapshots first.")
    frames: List[List[int]] = []
    with snap_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            try:
                frame = [int(x) for x in parts]
                frames.append(frame)
            except Exception:
                continue
    if not frames:
        raise RuntimeError(f"No frames parsed from {snap_path}")
    return frames


def generate_snapshots_if_needed(algo: str, graph_name: str, graph_file: Path, args: argparse.Namespace) -> None:
    """Run the C++ benchmark runner to produce snapshot file if missing or empty."""
    snap_path = SNAP_DIR / f"{algo}-{graph_name}-snnapshots.txt"
    if snap_path.exists() and snap_path.stat().st_size > 0:
        return
    if not BENCH.exists():
        raise FileNotFoundError(f"Runner binary not found at {BENCH}. Build it first (make all).")
    SNAP_DIR.mkdir(parents=True, exist_ok=True)
    # Ensure raw results dir exists
    (ROOT / "results" / "raw").mkdir(parents=True, exist_ok=True)
    out_col = ROOT / "results" / "raw" / f"{graph_name}_{algo}.col"
    results_csv = ROOT / "results" / "results.csv"
    cmd = [str(BENCH), "--algorithm", algo, "--input", str(graph_file), "--output", str(out_col), "--results", str(results_csv), "--graph-name", graph_name, "--save-snapshots"]

    # Algorithm-specific flags (only if runner is extended later; current C++ ignores these if not implemented)
    if algo == "genetic":
        cmd.extend(["--population-size", str(args.population_size), "--generations", str(args.generations), "--mutation-rate", str(args.mutation_rate)])
    if algo == "exact_solver" and args.exact_progress_interval is not None:
        # Use environment variable EXACT_PROGRESS_INTERVAL
        env = dict(**os.environ)
        env["EXACT_PROGRESS_INTERVAL"] = str(args.exact_progress_interval)
    else:
        env = None
    print("[animate] Running:", " ".join(cmd))
    completed = subprocess.run(cmd, cwd=ROOT, env=env)
    if completed.returncode != 0:
        raise RuntimeError(f"benchmark_runner exited with code {completed.returncode}")
    if not snap_path.exists() or snap_path.stat().st_size == 0:
        raise RuntimeError(f"Snapshot file not created: {snap_path}")


def circular_layout(n: int) -> List[Tuple[float,float]]:
    angle_step = 2 * math.pi / n if n else 0
    return [(math.cos(i * angle_step), math.sin(i * angle_step)) for i in range(n)]

def spring_layout(n: int, edges: List[Tuple[int,int]], seed: int) -> List[Tuple[float,float]]:
    if nx is None:
        return circular_layout(n)
    G = nx.Graph()
    G.add_nodes_from(range(n))
    G.add_edges_from(edges)
    pos = nx.spring_layout(G, seed=seed)
    # Normalize positions to roughly unit disk
    xs = [pos[i][0] for i in range(n)]
    ys = [pos[i][1] for i in range(n)]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    span_x = max_x - min_x or 1.0
    span_y = max_y - min_y or 1.0
    return [((pos[i][0]-min_x)/span_x*2-1, (pos[i][1]-min_y)/span_y*2-1) for i in range(n)]


def animate(frames: List[List[int]], interval: float, repeat: bool, layout: str, seed: int, edges: List[Tuple[int,int]], manual: bool):
    n = len(frames[0])
    if layout == 'spring':
        pos = spring_layout(n, edges, seed)
    else:
        pos = circular_layout(n)

    fig, ax = plt.subplots(figsize=(7,7))
    ax.set_axis_off()

    # Draw edges once
    if edges:
        edge_segments = [ [pos[u], pos[v]] for u,v in edges ]
        from matplotlib.collections import LineCollection
        lc = LineCollection(edge_segments, colors='#999999', linewidths=1, zorder=1)
        ax.add_collection(lc)

    scat = ax.scatter([p[0] for p in pos], [p[1] for p in pos], c=['#cccccc']*n, s=320, edgecolors='black', linewidths=0.7, zorder=2)
    title = ax.set_title("Frame 0")

    def colour_to_rgba(c: int) -> str:
        if c < 0:
            return '#cccccc'
        return PALETTE[c % len(PALETTE)]

    frame_index = 0
    def update(frame_idx: int):
        colours = [colour_to_rgba(c) for c in frames[frame_idx]]
        scat.set_color(colours)
        title.set_text(f"Iteration {frame_idx+1}/{len(frames)}")

    if manual:
        update(frame_index)
        def on_key(event):
            nonlocal frame_index
            if event.key in ("enter", "return", "space", "right", "k"):
                if frame_index < len(frames) - 1:
                    frame_index += 1
                    update(frame_index)
                else:
                    if repeat:
                        frame_index = 0
                        update(frame_index)
                    else:
                        plt.close(fig)
            elif event.key in ("left", "h"):
                if frame_index > 0:
                    frame_index -= 1
                    update(frame_index)
                else:
                    if repeat:
                        frame_index = len(frames) - 1
                        update(frame_index)
            elif event.key in ("q", "escape"):
                plt.close(fig)
        fig.canvas.mpl_connect('key_press_event', on_key)
        plt.show()
    else:
        try:
            while True:
                update(frame_index)
                plt.pause(interval)
                frame_index += 1
                if frame_index >= len(frames):
                    if repeat:
                        frame_index = 0
                    else:
                        break
        except KeyboardInterrupt:
            pass
        plt.show()


def animate_multi(frames_map: Dict[str, List[List[int]]], interval: float, sa_interval: float | None,
                  repeat: bool, layout: str, seed: int, edges: List[Tuple[int,int]], manual: bool):
    algos = list(frames_map.keys())
    max_len = max(len(frames) for frames in frames_map.values())
    n_vertices = {a: len(frames_map[a][0]) for a in algos}
    
    # Layout positions (shared across all assuming same graph)
    if layout == 'spring':
        pos = spring_layout(list(n_vertices.values())[0], edges, seed)
    else:
        pos = circular_layout(list(n_vertices.values())[0])
    cols = 3
    rows = 2
    fig, axes = plt.subplots(rows, cols, figsize=(cols*4.0, rows*4.0))
    axes_flat = axes.flatten()
    for ax in axes_flat[len(algos):]:
        ax.set_visible(False)
    # pre-draw edges and scatter per subplot
    scatters = {}
    titles = {}
    for idx, algo in enumerate(algos):
        ax = axes_flat[idx]
        ax.set_axis_off()
        if edges:
            edge_segments = [[pos[u], pos[v]] for u,v in edges]
            from matplotlib.collections import LineCollection
            lc = LineCollection(edge_segments, colors='#999999', linewidths=1, zorder=1)
            ax.add_collection(lc)
        scat = ax.scatter([p[0] for p in pos], [p[1] for p in pos], c=['#cccccc']*len(pos), s=200, edgecolors='black', linewidths=0.5, zorder=2)
        scatters[algo] = scat
        titles[algo] = ax.set_title(f"{algo}: frame 0")

    def colour_to_rgba(c: int) -> str:
        if c < 0:
            return '#cccccc'
        return PALETTE[c % len(PALETTE)]

    # Per-algo frame indices and intervals
    frame_indices = {algo: 0 for algo in algos}
    now = time.time()
    last_update = {algo: now for algo in algos}
    # per-algo interval: SA gets sa_interval if provided, else falls back to interval
    per_algo_interval = {algo: (sa_interval if (algo == "simulated_annealing" and sa_interval is not None) else interval) for algo in algos}

    def update_algo(algo: str):
        idx = frame_indices[algo]
        frames = frames_map[algo]
        use_idx = min(idx, len(frames)-1)
        colours = [colour_to_rgba(c) for c in frames[use_idx]]
        scatters[algo].set_color(colours)
        titles[algo].set_text(f"{algo}: {use_idx+1}/{len(frames)}")

    if manual:
        # Manual stepping advances all algos together using max_len
        frame_index = 0
        def update_all(idx: int):
            for algo in algos:
                # clamp to each algo's length
                frames = frames_map[algo]
                use_idx = min(idx, len(frames)-1)
                colours = [colour_to_rgba(c) for c in frames[use_idx]]
                scatters[algo].set_color(colours)
                titles[algo].set_text(f"{algo}: {use_idx+1}/{len(frames)}")
        update_all(frame_index)
        def on_key(event):
            nonlocal frame_index
            if event.key in ("enter", "return", "space", "right", "k"):
                if frame_index < max_len - 1:
                    frame_index += 1
                    update_all(frame_index)
                else:
                    if repeat:
                        frame_index = 0
                        update_all(frame_index)
                    else:
                        plt.close(fig)
            elif event.key in ("left", "h"):
                if frame_index > 0:
                    frame_index -= 1
                    update_all(frame_index)
                else:
                    if repeat:
                        frame_index = max_len - 1
                        update_all(frame_index)
            elif event.key in ("q", "escape"):
                plt.close(fig)
        fig.canvas.mpl_connect('key_press_event', on_key)
        plt.show()
    else:
        try:
            # Main loop: each algo advances when its interval has elapsed
            while True:
                t = time.time()
                # advance each algo independently if its interval elapsed
                any_changed = False
                for algo in algos:
                    if len(frames_map[algo]) == 0:
                        continue
                    if per_algo_interval[algo] <= 0:
                        # guard: non-positive interval treated as immediate advance each iteration
                        should_advance = True
                    else:
                        should_advance = (t - last_update[algo]) >= per_algo_interval[algo]
                    if should_advance:
                        last_update[algo] = t
                        # advance index
                        if frame_indices[algo] < len(frames_map[algo]) - 1:
                            frame_indices[algo] += 1
                        else:
                            # reached end for this algo
                            if repeat:
                                frame_indices[algo] = 0
                            else:
                                # clamp to last frame (do not wrap)
                                frame_indices[algo] = len(frames_map[algo]) - 1
                        update_algo(algo)
                        any_changed = True
                # If nothing changed (intervals small), still sleep a tiny bit to avoid busy loop
                if not any_changed:
                    time.sleep(min(0.01, max(0.001, min(per_algo_interval.values()) / 10.0)))
                # Determine termination condition: if none are set to repeat and all reached their final frames, break
                if not repeat:
                    all_done = all(frame_indices[algo] >= (len(frames_map[algo]) - 1) for algo in algos)
                    if all_done:
                        break
                # let matplotlib update its event loop and rendering
                plt.pause(0.001)
        except KeyboardInterrupt:
            pass
        plt.show()


def main() -> int:
    args = parse_args()
    graph_file, graph_name = resolve_graph_path_and_name(args.graph)
    vertex_count, edges = read_graph(graph_file)
    all_algos_mode = getattr(args, 'all_algos', False)
    
    if all_algos_mode:
        all_algos = ["dsatur", "welsh_powell", "genetic", "simulated_annealing", "exact_solver"]
        frames_map: Dict[str, List[List[int]]] = {}
        for algo in all_algos:
            if not args.skip_run:
                generate_snapshots_if_needed(algo, graph_name, graph_file, args)
            frames_map[algo] = load_snapshots(algo, graph_name)
        # sanity: ensure consistent vertex count
        for algo, frames in frames_map.items():
            if len(frames[0]) != vertex_count:
                print(f"Warning: {algo} snapshot length {len(frames[0])} != graph vertex_count {vertex_count}")
        # In multi-algo mode: pass both intervals; animate_multi will use sa_interval for SA only
        animate_multi(frames_map, args.interval, args.sa_interval, args.repeat, args.layout, args.seed, edges, args.manual)
    else:
        if not args.skip_run:
            generate_snapshots_if_needed(args.algo, graph_name, graph_file, args)
        frames = load_snapshots(args.algo, graph_name)
        if len(frames[0]) != vertex_count:
            print(f"Warning: snapshot vector length {len(frames[0])} differs from vertex_count {vertex_count}. Using snapshot length.")
        # Use sa_interval only for simulated_annealing, otherwise use regular interval
        interval = args.sa_interval if (args.algo == "simulated_annealing" and args.sa_interval) else args.interval
        animate(frames, interval, args.repeat, args.layout, args.seed, edges, args.manual)
    return 0

if __name__ == "__main__":
    sys.exit(main())
