# Graph Colouring Benchmark Suite

Benchmark, compare, and analyze graph colouring algorithms on DIMACS and generated datasets. The suite provides a C++ runner that handles I/O, timing, and CSV logging, plus a Python orchestrator to run all algorithms across many graphs with timeouts and retries.

## Build

- Requirements: g++ with C++20, Python 3.8+
- Build the runner binary:
	- make all
	- Output: `build/benchmark_runner`

## Run a single algorithm

The runner loads a DIMACS graph, dispatches the chosen algorithm, writes the colouring, and appends a CSV row with metrics.

Example via Makefile targets (change `GRAPH=...`):

- make run-dsatur GRAPH=dimacs/myciel6.col
- make run-exact GRAPH=dimacs/myciel6.col

Direct CLI:

- build/benchmark_runner --algorithm dsatur --input scripts/datasets/dimacs/myciel6.col --output results/raw/myciel6_dsatur.col --results results/results.csv --graph-name myciel6

CLI options:

- --algorithm NAME          One of: welsh_powell, dsatur, simulated_annealing, genetic, exact_solver
- --input FILE              Path to DIMACS .col graph
- --output FILE             Where to write the colouring
- --results FILE            CSV to append metrics
- --graph-name NAME         Override graph identifier in CSV and filenames
- --known-optimal VALUE     Known chromatic number (optional; auto-filled from metadata when possible)

## End-to-end flow

Minimal data flow from graph file to outputs:

```mermaid
flowchart LR
    G[DIMACS .col file\n(p edge V E + e u v)] --> LG[load_graph()\n→ Graph{V,E,adj}]
    LG --> D{dispatch\nalgorithm name}
    D --> A[algorithm fn\n(const Graph&)->vector<int>\n(colours size=V)]
    A --> W[write_coloring()\n.col output\nv i color]
    A --> M[metrics build\ncolor_count,runtime_ms]
    MD[metadata CSVs\nknown_optimal] --> M
    M --> KO[known_optimal fill\nCLI or lookup]
    KO --> CSV[append_result_csv()\nresults.csv row]
```

## Function reference (I/O contracts)

Namespace: `graph_colouring`

Core I/O:
- load_graph(path) -> Graph
- write_coloring(path, graph, colors)
- append_result_csv(path, BenchmarkResult)

Algorithms (all: (const Graph&) -> std::vector<int>):
- colour_with_welsh_powell
- colour_with_dsatur
- colour_with_simulated_annealing
- colour_with_genetic
- colour_with_exact (env: EXACT_PROGRESS_INTERVAL for progress)

Metadata helper:
- lookup_known_optimal_from_metadata(name) -> std::optional<int>

## CSV outputs

- Per-run CSV (`results/results.csv`):
	- Header: `algorithm,graph_name,vertices,edges,colors_used,known_optimal,runtime_ms`
	- known_optimal is taken from CLI if provided, else auto-filled from metadata files when available

- Batch aggregate CSV (`results/run_all_results.csv`):
	- Header: `algorithm,graph_name,vertices,edges,colors_used,known_optimal,runtime_ms,status`
	- Status values: `ok`, `ok(retry)`, `timeout>45s`, `error`, and `ok(no-parse)` variants

## Run all benchmarks (timeouts + retry)

The Python orchestrator runs all algorithms over a set of graphs with robust timeouts and status reporting.

- make run-all-benchmarking
	- Builds if needed; runs `scripts/run_all_benchmarks.py --include-generated`
	- First pass timeout: 15s per job; retry timeouts with 30s; if still timing out, marks `timeout>45s`
	- Output: colouring files in `results/raw/` and aggregate CSV at `results/run_all_results.csv`

You can call the script directly for custom runs:

- python3 scripts/run_all_benchmarks.py --graphs scripts/datasets/dimacs/myciel6.col scripts/datasets/dimacs/queen6_6.col --first-timeout 10 --second-timeout 20

Order of algorithms per graph:

1) welsh_powell → 2) dsatur → 3) simulated_annealing → 4) genetic → 5) exact_solver

## Environment variables

- EXACT_PROGRESS_INTERVAL
	- Controls stderr progress print interval in seconds for the exact solver
	- Valid range: 0.05 to 600; default 5.0

## Project layout (selected)

- src/
	- benchmark_runner.cpp: CLI parsing, algorithm dispatch, timing, metadata lookup, CSV logging
	- algorithms/: colouring implementations (dsatur, genetic, exact_solver; others scaffolded)
	- io/: `graph_loader.cpp`, `graph_writer.cpp`, `results_logger.cpp`
	- utils.h: Graph and BenchmarkResult types and I/O declarations
- scripts/
	- run_all_benchmarks.py: batch runner with timeouts, retries, status aggregation
	- datasets/: DIMACS and generated graphs, plus metadata CSVs
- results/
	- raw/: per-run colouring outputs `*.col`
	- results.csv: ad-hoc runs
	- run_all_results.csv: aggregated batch results

## Notes and next steps

- Welsh-Powell and Simulated Annealing are currently placeholders; fill in their implementations or disable their runs in the orchestrator if undesired.
- The runner auto-fills `known_optimal` from metadata when not provided on CLI; ensure the metadata files list your graphs when possible.
- If you add a new algorithm, expose `std::vector<int> colour_with_<name>(const Graph&)`, include its header in `src/benchmark_runner.cpp`, add to `build_algorithm_table()`, and add a Makefile run target.

