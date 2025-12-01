#!/usr/bin/env python3
"""
Generate synthetic graphs for the colouring benchmark suite.

This module creates various families of synthetic graphs in DIMACS format
for testing graph colouring algorithms. Supports reproducible generation
via random seed and metadata logging.

Graph Families:
    - bipartite: Two-partition graphs (χ=2)
    - planar: Graphs drawable without edge crossings (χ≤4)
    - tree: Connected acyclic graphs (χ=2)
    - grid: 2D lattice/mesh topology (χ∈{2,3})
    - erdos_renyi: G(n,p) random graphs
    - barabasi_albert: Scale-free networks (preferential attachment)
    - watts_strogatz: Small-world networks
    - complete: Complete graphs Kₙ (χ=n)

Usage:
    python3 tools/generate_graphs.py
    python3 tools/generate_graphs.py --seed 42 --types tree grid --overwrite
"""

from __future__ import annotations

import argparse
import csv
import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable

import networkx as nx


@dataclass
class GenerationTask:
    """
    Configuration describing how to generate a batch of graphs.
    
    Attributes:
        kind: Graph family name (e.g., 'bipartite', 'tree').
        count: Number of graphs to generate for this family.
        builder: Function that creates a NetworkX graph given RNG and size.
        size_range: Tuple (min_vertices, max_vertices) for random sizing.
        notes: Description string for metadata CSV.
    """

    kind: str
    count: int
    builder: Callable[[random.Random, int], nx.Graph]
    size_range: tuple[int, int]
    notes: str


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments for graph generation.
    
    Returns:
        argparse.Namespace: Parsed arguments including target directory,
                           metadata path, random seed, overwrite flag, and graph types.
    """

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        type=Path,
        default=Path("data/generated"),
        help="Directory that receives generated .col files (default: data/generated)",
    )
    parser.add_argument(
        "--metadata",
        type=Path,
        default=Path("datasets/metadata.csv"),
        help="CSV file where metadata rows are appended (default: datasets/metadata.csv)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Seed for the pseudorandom generator (default: 42)",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Regenerate graphs even if files already exist",
    )
    parser.add_argument(
        "--types",
        nargs="*",
        choices=[
            "bipartite",
            "planar",
            "tree",
            "grid",
            "erdos_renyi",
            "barabasi_albert",
            "watts_strogatz",
            "complete",
        ],
        help="Subset of graph families to generate (default: all)",
    )
    return parser.parse_args()


def dimacs_write(graph: nx.Graph, destination: Path, title: str) -> None:
    """
    Write a NetworkX graph to a file in DIMACS edge format.
    
    Args:
        graph: The NetworkX graph to write.
        destination: Output file path (.col extension recommended).
        title: Comment string to include in the file header.
    """

    destination.parent.mkdir(parents=True, exist_ok=True)
    nodes = sorted(graph.nodes())
    mapping = {node: index + 1 for index, node in enumerate(nodes)}
    edges = sorted({tuple(sorted((mapping[u], mapping[v]))) for u, v in graph.edges() if u != v})

    lines = [f"c {title}", f"p edge {len(nodes)} {len(edges)}"]
    lines.extend(f"e {u} {v}" for u, v in edges)
    destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def ensure_connected(graph: nx.Graph) -> nx.Graph:
    """
    Extract the largest connected component from a graph.
    
    Args:
        graph: Input NetworkX graph (may be disconnected).
    
    Returns:
        nx.Graph: A copy containing only the largest connected component.
                 Returns the original if already connected or empty.
    """

    if graph.number_of_nodes() == 0:
        return graph
    if nx.is_connected(graph):
        return graph
    largest_nodes = max(nx.connected_components(graph), key=len)
    return graph.subgraph(largest_nodes).copy()


def choose_size(rng: random.Random, size_range: tuple[int, int]) -> int:
    """
    Sample a random vertex count within specified bounds.
    
    Args:
        rng: Random number generator instance.
        size_range: Tuple (min_size, max_size) inclusive bounds.
    
    Returns:
        int: Randomly chosen size within the range.
    """

    low, high = size_range
    return rng.randint(low, high)


def build_bipartite(rng: random.Random, n: int) -> nx.Graph:
    """
    Build a random bipartite graph with n vertices.
    
    Args:
        rng: Random number generator.
        n: Target number of vertices.
    
    Returns:
        nx.Graph: Connected bipartite graph (χ=2).
    """
    left = max(2, int(n * rng.uniform(0.4, 0.6)))
    right = max(2, n - left)
    p = rng.uniform(0.1, 0.3)
    graph = nx.bipartite.random_graph(left, right, p, seed=rng.randint(0, 1_000_000))
    return ensure_connected(nx.Graph(graph))


def build_planar(rng: random.Random, n: int) -> nx.Graph:
    """
    Build a random planar graph with n vertices.
    
    Starts with a random tree and adds edges while maintaining planarity.
    
    Args:
        rng: Random number generator.
        n: Target number of vertices.
    
    Returns:
        nx.Graph: Planar graph (χ≤4 by Four Color Theorem).
    """
    graph = nx.random_tree(n, seed=rng.randint(0, 1_000_000))
    max_edges = max(0, 3 * n - 6)
    target_edges = min(max_edges, graph.number_of_edges() + n)
    attempts = 0
    while graph.number_of_edges() < target_edges and attempts < 10 * n:
        u = rng.randrange(n)
        v = rng.randrange(n)
        if u == v or graph.has_edge(u, v):
            continue
        graph.add_edge(u, v)
        planar, _ = nx.check_planarity(graph)
        if not planar:
            graph.remove_edge(u, v)
        attempts += 1
    return graph


def build_tree(rng: random.Random, n: int) -> nx.Graph:
    """Generate a uniform random tree.

    Args:
        rng: Random number generator for reproducibility.
        n: Number of nodes in the tree.

    Returns:
        nx.Graph: A connected tree with n nodes and n-1 edges.
    """
    return nx.random_tree(n, seed=rng.randint(0, 1_000_000))


def build_grid(rng: random.Random, n: int) -> nx.Graph:
    """Generate a 2D grid graph.

    Args:
        rng: Random number generator (unused but kept for consistent API).
        n: Approximate number of nodes (actual count depends on factorization).

    Returns:
        nx.Graph: A 2D grid graph with approximately n nodes.
    """
    side = max(2, int(math.sqrt(n)))
    other = max(2, n // side)
    graph = nx.grid_2d_graph(side, other)
    relabelled = nx.convert_node_labels_to_integers(graph)
    return nx.Graph(relabelled)


def build_erdos_renyi(rng: random.Random, n: int) -> nx.Graph:
    """Generate an Erdos-Renyi random graph.

    Args:
        rng: Random number generator for reproducibility.
        n: Number of nodes in the graph.

    Returns:
        nx.Graph: A connected Erdos-Renyi random graph with edge probability in [0.05, 0.2].
    """
    p = rng.uniform(0.05, 0.2)
    graph = nx.erdos_renyi_graph(n, p, seed=rng.randint(0, 1_000_000))
    return ensure_connected(graph)


def build_barabasi_albert(rng: random.Random, n: int) -> nx.Graph:
    """Generate a Barabasi-Albert preferential attachment (scale-free) graph.

    Args:
        rng: Random number generator for reproducibility.
        n: Number of nodes in the graph.

    Returns:
        nx.Graph: A scale-free graph generated using preferential attachment.
    """
    m = max(2, min(5, n // 20))
    graph = nx.barabasi_albert_graph(n, m, seed=rng.randint(0, 1_000_000))
    return graph


def build_watts_strogatz(rng: random.Random, n: int) -> nx.Graph:
    """Generate a Watts-Strogatz small-world graph.

    Args:
        rng: Random number generator for reproducibility.
        n: Number of nodes in the graph.

    Returns:
        nx.Graph: A connected small-world graph with tunable clustering.
    """
    # Degree must be even and less than n.
    k = max(2, (n // 20) * 2)
    k = min(k, n - (1 - n % 2))
    beta = rng.uniform(0.05, 0.3)
    graph = nx.watts_strogatz_graph(n, max(2, k), beta, seed=rng.randint(0, 1_000_000))
    return ensure_connected(graph)


def build_complete(_: random.Random, n: int) -> nx.Graph:
    """Generate a complete graph K_n.

    Args:
        _: Random number generator (unused).
        n: Number of nodes in the graph.

    Returns:
        nx.Graph: A complete graph with n nodes and n*(n-1)/2 edges.
    """
    return nx.complete_graph(n)


def default_tasks() -> list[GenerationTask]:
    """Return the default generation plan.

    Returns:
        list[GenerationTask]: A list of predefined graph generation tasks covering
            various graph types (bipartite, planar, tree, grid, etc.).
    """
    return [
        GenerationTask("bipartite", 5, build_bipartite, (50, 1_000), "Random bipartite"),
        GenerationTask("planar", 5, build_planar, (50, 500), "Random planar"),
        GenerationTask("tree", 5, build_tree, (50, 1_000), "Uniform random tree"),
        GenerationTask("grid", 5, build_grid, (100, 2_500), "2D grid"),
        GenerationTask("erdos_renyi", 10, build_erdos_renyi, (100, 2_000), "Erdos-Renyi"),
        GenerationTask("barabasi_albert", 10, build_barabasi_albert, (100, 2_000), "Scale-free"),
        GenerationTask("watts_strogatz", 10, build_watts_strogatz, (100, 1_000), "Small-world"),
        GenerationTask("complete", 5, build_complete, (10, 100), "Complete graph"),
    ]


def filter_tasks(tasks: Iterable[GenerationTask], allowed: Iterable[str] | None) -> list[GenerationTask]:
    """Filter generation tasks by allowed graph types.

    Args:
        tasks: Iterable of GenerationTask objects.
        allowed: Collection of allowed graph type names, or None to allow all.

    Returns:
        list[GenerationTask]: Filtered list containing only tasks with allowed types.
    """
    if not allowed:
        return list(tasks)
    allowed_set = {kind.lower() for kind in allowed}
    return [task for task in tasks if task.kind.lower() in allowed_set]


def load_existing_metadata(metadata_path: Path) -> set[str]:
    """Load existing graph names from a metadata CSV file.

    Args:
        metadata_path: Path to the metadata CSV file.

    Returns:
        set[str]: Set of graph names already present in the metadata file.
    """
    if not metadata_path.exists():
        return set()
    with metadata_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            return set()
        return {row.get("graph_name", "") for row in reader}


def append_metadata(
    metadata_path: Path,
    row: dict[str, object],
    has_header: bool,
) -> None:
    """Append a metadata row to the CSV file.

    Args:
        metadata_path: Path to the metadata CSV file.
        row: Dictionary containing graph metadata fields.
        has_header: Whether the file already has a header row.
    """
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    mode = "a" if metadata_path.exists() else "w"
    with metadata_path.open(mode, encoding="utf-8", newline="") as handle:
        fieldnames = [
            "graph_name",
            "source",
            "vertices",
            "edges",
            "density",
            "known_optimal",
            "path",
            "graph_type",
            "notes",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if mode == "w" or not has_header:
            writer.writeheader()
        writer.writerow(row)


def compute_density(vertices: int, edges: int) -> float:
    """Compute the density of an undirected graph.

    Args:
        vertices: Number of vertices in the graph.
        edges: Number of edges in the graph.

    Returns:
        float: Graph density as ratio of actual edges to maximum possible edges.
    """
    if vertices <= 1:
        return 0.0
    return (2.0 * edges) / (vertices * (vertices - 1))


def main() -> None:
    """Main entry point for graph generation.

    Parses command-line arguments, generates graphs according to the
    specified configuration, writes them in DIMACS format, and updates
    the metadata CSV file.
    """
    args = parse_args()
    rng = random.Random(args.seed)

    tasks = filter_tasks(default_tasks(), args.types)
    if not tasks:
        print("No tasks selected; exiting.")
        return

    existing = load_existing_metadata(args.metadata)
    metadata_has_header = args.metadata.exists() and args.metadata.read_text(encoding="utf-8").strip() != ""

    generated_count = 0
    for task in tasks:
        for index in range(task.count):
            n = choose_size(rng, task.size_range)
            graph = task.builder(rng, n)
            graph = ensure_connected(graph)
            n = graph.number_of_nodes()
            m = graph.number_of_edges()
            if n == 0:
                print(f"skip {task.kind}#{index}: empty graph", file=sys.stderr)
                continue

            filename = f"{task.kind}_{n}_{index+1}.col"
            destination = args.target / filename
            if destination.exists() and not args.overwrite:
                print(f"skip {filename} (exists)")
                continue

            dimacs_write(graph, destination, f"Generated {task.kind} graph")
            generated_count += 1

            if filename not in existing or args.overwrite:
                row = {
                    "graph_name": filename,
                    "source": "generated",
                    "vertices": n,
                    "edges": m,
                    "density": f"{compute_density(n, m):.6f}",
                    "known_optimal": "",
                    "path": str(destination.relative_to(Path.cwd()) if destination.is_absolute() else destination),
                    "graph_type": task.kind,
                    "notes": task.notes,
                }
                append_metadata(args.metadata, row, metadata_has_header)
                metadata_has_header = True
                existing.add(filename)

    print(f"Generated {generated_count} graph(s) in {args.target}")


if __name__ == "__main__":
	main()
