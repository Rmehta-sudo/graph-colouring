# Graph Colouring Benchmark Suite

Benchmark, compare, and analyze graph colouring algorithms on DIMACS and generated datasets. The suite provides a C++ runner that handles I/O, timing, and CSV logging, plus a Python orchestrator to run all algorithms across many graphs with timeouts and retries.

## Algorithms Implemented

| Algorithm | Type | Time Complexity | Description |
|-----------|------|-----------------|-------------|
| Welsh-Powell | Greedy | O(V log V + E) | Degree-ordered greedy |
| DSatur | Greedy | O(V² + E) | Saturation-based greedy |
| Simulated Annealing | Metaheuristic | Configurable | Temperature-based optimization |
| Genetic Algorithm | Metaheuristic | O(P × G × V) | Evolutionary approach |
| Tabu Search | Metaheuristic | O(I × V × k) | TabuCol with conflict repair |
| Exact Solver | Exact | Exponential | Branch & bound (small graphs) |

## Quick Start

```bash
# Build
make all

# Run single algorithm
make run-dsatur GRAPH=dimacs/myciel6.col
make run-tabu GRAPH=dimacs/myciel6.col

# Run all benchmarks
make run-all-benchmarking

# Animate algorithm progress
python3 tools/animate_coloring.py --graph myciel6 --algo dsatur
```

## Build

**Requirements:** g++ with C++20, Python 3.8+, matplotlib, networkx (for animation)

```bash
make all           # Build benchmark_runner
make clean         # Clean build artifacts
```

## Usage

### Single Algorithm Run

```bash
# Via Makefile (recommended)
make run-dsatur GRAPH=dimacs/myciel6.col
make run-tabu GRAPH=generated/tree_275_4.col SNAPSHOTS=1

# Direct CLI
./build/benchmark_runner \
    --algorithm tabu_search \
    --input data/dimacs/myciel6.col \
    --output results/colourings/myciel6_tabu.col \
    --results results/results.csv \
    --graph-name myciel6 \
    --save-snapshots
```

**CLI Options:**

| Option | Description |
|--------|-------------|
| `--algorithm NAME` | welsh_powell, dsatur, simulated_annealing, genetic, tabu_search, exact_solver |
| `--input FILE` | Path to DIMACS .col graph |
| `--output FILE` | Where to write the colouring |
| `--results FILE` | CSV to append metrics |
| `--graph-name NAME` | Override graph identifier |
| `--save-snapshots` | Save per-iteration state for animation |

### Batch Benchmarking

```bash
# Run all algorithms on all graphs
make run-all-benchmarking

# Custom run
python3 tools/run_all_benchmarks.py \
    --graphs data/dimacs/myciel6.col data/dimacs/queen6_6.col \
    --first-timeout 15 \
    --second-timeout 30
```

### Animation

Visualize algorithm progress:

```bash
python3 tools/animate_coloring.py --graph myciel6 --algo dsatur
python3 tools/animate_coloring.py --graph myciel6 --algo tabu_search --interval 0.05
python3 tools/animate_coloring.py --graph myciel6 --all-algos  # Compare all
```

## Project Structure

```
graph-colouring/
├── README.md
├── Makefile
│
├── src/                        # C++ source code
│   ├── benchmark_runner.cpp    # Main CLI entry point
│   ├── utils.h                 # Core types (Graph, BenchmarkResult)
│   ├── algorithms/             # Colouring algorithms
│   │   ├── dsatur.cpp/.h
│   │   ├── welsh_powell.cpp/.h
│   │   ├── genetic.cpp/.h
│   │   ├── simulated_annealing.cpp/.h
│   │   ├── tabu.cpp/.h
│   │   └── exact_solver.cpp/.h
│   └── io/                     # File I/O utilities
│       ├── graph_loader.cpp/.h
│       ├── graph_writer.cpp/.h
│       └── results_logger.cpp/.h
│
├── tools/                      # Python tools
│   ├── run_all_benchmarks.py   # Batch runner with timeouts
│   ├── animate_coloring.py     # Algorithm visualization
│   ├── generate_graphs.py      # Synthetic graph generator
│   └── analysis/               # Result analysis scripts
│
├── data/                       # Graph datasets
│   ├── dimacs/                 # DIMACS benchmark graphs
│   ├── generated/              # Synthetic test graphs
│   ├── network-repo/           # Network repository graphs
│   ├── metadata-dimacs.csv
│   └── metadata-generated.csv
│
├── results/                    # Benchmark outputs
│   ├── colourings/             # Per-run colouring files
│   ├── results.csv             # Single-run metrics
│   └── run_all_results.csv     # Batch run aggregate
│
├── output/                     # Generated outputs
│   ├── snapshots/              # Algorithm state snapshots
│   └── animations/             # Animation videos
│
├── docs/                       # Documentation
│   ├── PROJECT_SUMMARY.md      # Detailed project documentation
│   ├── code-spec.md            # Code specifications
│   └── references/             # Academic papers
│
├── legacy/                     # Old/utility scripts
│
└── build/                      # Compiled binaries (gitignored)
```

## Output Format

### Results CSV

```csv
algorithm,graph_name,vertices,edges,colors_used,known_optimal,runtime_ms
dsatur,myciel6,95,755,7,7,0.234
tabu_search,myciel6,95,755,7,7,45.123
```

### Status Values (Batch Runs)

- `ok` - Completed successfully
- `ok(retry)` - Completed on second attempt
- `timeout>45s` - Exceeded timeout limits
- `error` - Non-zero exit code

## Documentation

- **[USAGE.md](docs/USAGE.md)** - Comprehensive usage guide with all commands
- **[PROJECT_SUMMARY.md](docs/PROJECT_SUMMARY.md)** - Detailed project documentation
- **[code-spec.md](docs/code-spec.md)** - Technical specifications

## License

AAD Coursework Project - Semester 3
