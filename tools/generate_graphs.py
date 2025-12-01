#!/usr/bin/env python3
"""Generate synthetic graphs for the colouring benchmark suite."""

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
	"""Configuration describing how to generate a batch of graphs."""

	kind: str
	count: int
	builder: Callable[[random.Random, int], nx.Graph]
	size_range: tuple[int, int]
	notes: str


def parse_args() -> argparse.Namespace:
	"""Parse CLI options."""

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
	"""Persist a graph in DIMACS edge format."""

	destination.parent.mkdir(parents=True, exist_ok=True)
	nodes = sorted(graph.nodes())
	mapping = {node: index + 1 for index, node in enumerate(nodes)}
	edges = sorted({tuple(sorted((mapping[u], mapping[v]))) for u, v in graph.edges() if u != v})

	lines = [f"c {title}", f"p edge {len(nodes)} {len(edges)}"]
	lines.extend(f"e {u} {v}" for u, v in edges)
	destination.write_text("\n".join(lines) + "\n", encoding="utf-8")


def ensure_connected(graph: nx.Graph) -> nx.Graph:
	"""Return the largest connected component as a copy."""

	if graph.number_of_nodes() == 0:
		return graph
	if nx.is_connected(graph):
		return graph
	largest_nodes = max(nx.connected_components(graph), key=len)
	return graph.subgraph(largest_nodes).copy()


def choose_size(rng: random.Random, size_range: tuple[int, int]) -> int:
	"""Sample a vertex count within the specified bounds."""

	low, high = size_range
	return rng.randint(low, high)


def build_bipartite(rng: random.Random, n: int) -> nx.Graph:
	left = max(2, int(n * rng.uniform(0.4, 0.6)))
	right = max(2, n - left)
	p = rng.uniform(0.1, 0.3)
	graph = nx.bipartite.random_graph(left, right, p, seed=rng.randint(0, 1_000_000))
	return ensure_connected(nx.Graph(graph))


def build_planar(rng: random.Random, n: int) -> nx.Graph:
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
	return nx.random_tree(n, seed=rng.randint(0, 1_000_000))


def build_grid(rng: random.Random, n: int) -> nx.Graph:
	side = max(2, int(math.sqrt(n)))
	other = max(2, n // side)
	graph = nx.grid_2d_graph(side, other)
	relabelled = nx.convert_node_labels_to_integers(graph)
	return nx.Graph(relabelled)


def build_erdos_renyi(rng: random.Random, n: int) -> nx.Graph:
	p = rng.uniform(0.05, 0.2)
	graph = nx.erdos_renyi_graph(n, p, seed=rng.randint(0, 1_000_000))
	return ensure_connected(graph)


def build_barabasi_albert(rng: random.Random, n: int) -> nx.Graph:
	m = max(2, min(5, n // 20))
	graph = nx.barabasi_albert_graph(n, m, seed=rng.randint(0, 1_000_000))
	return graph


def build_watts_strogatz(rng: random.Random, n: int) -> nx.Graph:
	# Degree must be even and less than n.
	k = max(2, (n // 20) * 2)
	k = min(k, n - (1 - n % 2))
	beta = rng.uniform(0.05, 0.3)
	graph = nx.watts_strogatz_graph(n, max(2, k), beta, seed=rng.randint(0, 1_000_000))
	return ensure_connected(graph)


def build_complete(_: random.Random, n: int) -> nx.Graph:
	return nx.complete_graph(n)


def default_tasks() -> list[GenerationTask]:
	"""Return the default generation plan."""

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
	if not allowed:
		return list(tasks)
	allowed_set = {kind.lower() for kind in allowed}
	return [task for task in tasks if task.kind.lower() in allowed_set]


def load_existing_metadata(metadata_path: Path) -> set[str]:
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
	if vertices <= 1:
		return 0.0
	return (2.0 * edges) / (vertices * (vertices - 1))


def main() -> None:
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
