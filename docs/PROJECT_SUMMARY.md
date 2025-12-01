# Graph Colouring Benchmark Suite - Project Summary# Graph Colouring Benchmark Suite - Project Summary



## Overview## Overview



This is an **Advanced Algorithm Design (AAD)** coursework project that implements and benchmarks various graph colouring algorithms. Graph colouring is an NP-hard problem where the goal is to assign colours to vertices such that no two adjacent vertices share the same colour, using as few colours as possible (the **chromatic number** χ(G)).This is an **Advanced Algorithm Design (AAD)** coursework project that implements and benchmarks various graph colouring algorithms. Graph colouring is an NP-hard problem where the goal is to assign colours to vertices such that no two adjacent vertices share the same colour, using as few colours as possible (the **chromatic number**).



------



## Project Structure## Project Structure



### Root Directory| Directory | Purpose |

|-----------|---------|

| File | Description || `src/` | C++ source code |

|------|-------------|| `src/algorithms/` | Graph colouring algorithm implementations |

| `README.md` | Project overview, quick start guide, and build instructions || `src/io/` | Graph loading, colouring output, and CSV result logging |

| `Makefile` | Build system with targets for compiling and running algorithms || `scripts/` | Python utilities for benchmarking, graph generation, and animation |

| `.gitignore` | Git ignore rules for build artifacts, Python cache, virtual environments || `scripts/datasets/` | DIMACS and generated graph files with metadata |

| `results/` | Output colourings and CSV benchmark results |

### Source Code (`src/`)| `snapshots-colouring/` | Step-by-step algorithm state snapshots for visualization |

| `info/` | Documentation and citations |

The C++ implementation of the benchmark framework and colouring algorithms.

---

| File | Description |

|------|-------------|## Implemented Algorithms

| `benchmark_runner.cpp` | **Main entry point** - CLI parsing, algorithm dispatch, timing, CSV logging. Handles `--algorithm`, `--input`, `--output`, `--save-snapshots` flags |

| `utils.h` | Core type definitions: `Graph` struct (vertex_count, edge_count, adjacency_list), `BenchmarkResult` struct, I/O function declarations || Algorithm | Type | Description |

|-----------|------|-------------|

#### Algorithms (`src/algorithms/`)| **Welsh-Powell** | Greedy heuristic | Orders vertices by degree, assigns lowest available colour |

| **DSatur** | Greedy heuristic | Prioritizes vertices with most distinct neighbour colours (saturation) |

Each algorithm has a `.h` header and `.cpp` implementation file.| **Simulated Annealing** | Metaheuristic | Temperature-based probabilistic acceptance of worse solutions |

| **Genetic Algorithm** | Evolutionary | Population-based with crossover, mutation, and selection |

| File | Algorithm | Description || **Exact Solver** | Branch-and-bound | Guarantees optimal chromatic number |

|------|-----------|-------------|| **Tabu Search** | Metaheuristic | TabuCol algorithm - iterative conflict repair with memory-based cycle prevention |

| `welsh_powell.cpp/.h` | Welsh-Powell | Greedy algorithm that orders vertices by degree (highest first) and assigns the lowest available colour. O(V log V + E) |

| `dsatur.cpp/.h` | DSatur | Saturation-based greedy. Prioritizes vertices with most distinct neighbour colours. Often produces near-optimal results. O(V² + E) |### Tabu Search (TabuCol) - Details

| `simulated_annealing.cpp/.h` | Simulated Annealing | Metaheuristic using temperature-based probabilistic acceptance of worse solutions to escape local optima |

| `genetic.cpp/.h` | Genetic Algorithm | Evolutionary approach with population, crossover, mutation, and selection. Includes GPX-lite crossover and adaptive mutation |The **Tabu Search** algorithm is an industry-standard metaheuristic for graph colouring that was added to address the performance limitations of the Genetic Algorithm.

| `tabu.cpp/.h` | Tabu Search (TabuCol) | Industry-standard metaheuristic. Iterative conflict repair with memory-based tabu list to prevent cycling |

| `exact_solver.cpp/.h` | Exact Solver | Branch-and-bound algorithm guaranteeing optimal chromatic number. Only practical for small graphs (<50 vertices) |**Strategy:**

1. Start with a random k-colouring (may have conflicts)

#### I/O Utilities (`src/io/`)2. Iteratively select a conflicting vertex and move it to the colour that minimizes conflicts

3. Mark the move (vertex, old_colour) as "tabu" for a tenure period to prevent cycling back

| File | Description |4. Accept the best non-tabu move; allow tabu moves only if they achieve a new global best (aspiration criterion)

|------|-------------|5. If zero conflicts achieved, decrease k and restart

| `graph_loader.cpp/.h` | Parses DIMACS `.col` format. Handles `p edge V E` header and `e u v` edge lines. Returns `Graph` struct |6. Stop when no feasible k-colouring found within iteration limit

| `graph_writer.cpp/.h` | Writes colouring output in DIMACS format with `v vertex colour` lines |

| `results_logger.cpp/.h` | Appends benchmark metrics to CSV files. Handles header creation and row formatting |**Key Parameters:**

- `max_iterations`: Maximum iterations per k value (default: 10000 or 100×|V|)

### Python Tools (`tools/`)- `tabu_tenure`: Number of iterations a move stays forbidden (default: 7 or |V|/10)



Python utilities for orchestration, visualization, and graph generation.**Why TabuCol over Genetic Algorithm:**

- More efficient: avoids expensive population management

| File | Description |- Better escape from local optima via tabu list memory

|------|-------------|- Industry-proven for graph colouring benchmarks

| `run_all_benchmarks.py` | **Batch orchestrator** - Runs all algorithms on all graphs with timeout handling (15s first pass, 30s retry). Aggregates results to `run_all_results.csv` |- Faster convergence on hard instances

| `animate_coloring.py` | **Visualization tool** - Animates colouring progression from snapshots. Supports manual stepping, timing control, all-algos comparison mode |

| `generate_graphs.py` | **Graph generator** - Creates synthetic graphs using NetworkX (bipartite, planar, tree, grid, Erdős-Rényi, Barabási-Albert, Watts-Strogatz, complete) |---



#### Analysis (`tools/analysis/`)## Datasets



| File | Description |### DIMACS Benchmarks (`scripts/datasets/dimacs/`)

|------|-------------|- **81 standard graphs** from the DIMACS graph colouring challenge

| `family_graphs.py` | Aggregates benchmark results by graph family (e.g., all queen graphs, all DSJC graphs) for comparative analysis |- Types: queen graphs, mycielski, flat, DSJ random, register allocation, school scheduling

- Metadata in `metadata-dimacs.csv`

### Datasets (`data/`)

### Generated Graphs (`scripts/datasets/generated/`)

Graph files in DIMACS edge format and associated metadata.- **55 synthetic graphs** created using NetworkX

- Types: bipartite, planar, tree, grid, Erdős-Rényi, Barabási-Albert (scale-free), Watts-Strogatz (small-world)

| Directory/File | Description |- Metadata in `metadata-generated.csv`

|----------------|-------------|

| `dimacs/` | **81 DIMACS benchmark graphs** - Standard test cases including queen, mycielski, DSJC random, flat, register allocation, scheduling graphs |### Simple Tests (`scripts/datasets/simple-tests/`)

| `generated/` | **55 synthetic graphs** - Created by `generate_graphs.py` covering various graph families and sizes |- 3 small test graphs: `cycle10.col`, `k-12.col` (complete K₁₂), `k-12plus.col`

| `network-repo/` | Additional graphs from network repositories |

| `simple-tests/` | **3 small test graphs** - `cycle10.col`, `k-12.col` (complete K₁₂), `k-12plus.col` for quick testing |---

| `metadata-dimacs.csv` | Known optimal chromatic numbers and graph properties for DIMACS graphs |

| `metadata-generated.csv` | Properties of generated graphs (vertices, edges, type, known optimal if applicable) |## Input/Output Formats



### Results (`results/`)### Input (DIMACS `.col` format)

```

Output from benchmark runs.c Comments

p edge 11 20          # 11 vertices, 20 edges

| File/Directory | Description |e 1 2                 # Edge from vertex 1 to 2

|----------------|-------------|e 1 4

| `results.csv` | Metrics from individual/ad-hoc runs via Makefile targets |...

| `run_all_results.csv` | Aggregate results from `run_all_benchmarks.py` with status column (ok, timeout, error) |```

| `graph_family_best_analysis.csv` | Per-family performance analysis showing which algorithm performs best |

| `colourings/` | ~330 colouring output files named `<graph>_<algorithm>.col` |### Colouring Output

```

### Output (`output/`)c colouring generated by benchmark framework

p edge 11 20

Generated visualization data and media.v 1 1                 # Vertex 1 has colour 1

v 2 0                 # Vertex 2 has colour 0

| Directory | Description |...

|-----------|-------------|```

| `snapshots/` | Algorithm state snapshots (`<algo>-<graph>-snapshots.txt`). Each line is a space-separated colour vector |

| `animations/` | Saved animation videos (if exported from animate_coloring.py) |### Results CSV

```csv

### Documentation (`docs/`)algorithm,graph_name,vertices,edges,colors_used,known_optimal,runtime_ms,status

dsatur,myciel6,95,755,7,7,0.135,ok

| File | Description |```

|------|-------------|

| `PROJECT_SUMMARY.md` | This file - comprehensive project documentation |---

| `USAGE.md` | Detailed usage guide with examples for all commands |

| `code-spec.md` | Technical specifications and API contracts |## Snapshots for Visualization

| `references/` | Academic papers: `Cache_me_if_you_can_10.pdf`, `marking-scheme.pdf`, `Dataset_Metadata_AAD_citations.pdf` |

The `snapshots-colouring/` directory contains **57 snapshot files** named `<algorithm>-<graph>-snnapshots.txt`.

### Legacy (`legacy/`)

**Format**: Each line is a space-separated colour vector:

Old utility scripts kept for reference.- `-1` = uncoloured vertex

- `0, 1, 2, ...` = assigned colour

| File | Description |

|------|-------------|**Example** (`dsatur-myciel3-snnapshots.txt`):

| `fetch_dimacs.py` | Downloads DIMACS graphs from web sources |```

| `fetch_dimacs_network_repo.py` | Downloads graphs from network repository |-1 -1 -1 -1 -1 -1 -1 -1 -1 -1 0    # Step 1: vertex 10 gets colour 0

| `convert_dimacs_binaries.py` | Converts binary DIMACS format to text |-1 -1 -1 -1 -1 1 -1 -1 -1 -1 0     # Step 2: vertex 5 gets colour 1

| `unzip_dimacs.py` | Extracts compressed DIMACS archives |...

| `bin2asc.c`, `genbin.h`, `binformat.shar` | C utilities for binary format conversion |1 0 1 2 0 1 2 1 2 3 0              # Final colouring

```

### Build (`build/`)

Used by `scripts/animate_coloring.py` to visualize algorithm progression.

Compiled artifacts (gitignored).

---

| File | Description |

|------|-------------|## Results & Analysis

| `benchmark_runner` | Main executable binary |

| `*.o` | Object files organized by source directory structure |### Output Files (`results/`)



---| File | Description |

|------|-------------|

## Implemented Algorithms| `results.csv` | Ad-hoc single runs |

| `run_all_results.csv` | Batch benchmark results (319 rows) with timeout status |

| Algorithm | Type | Time Complexity | Description || `graph_family_best_analysis.csv` | Per-family performance analysis |

|-----------|------|-----------------|-------------|| `family_graphs.py` | Aggregation script for family-level analysis |

| **Welsh-Powell** | Greedy | O(V log V + E) | Orders vertices by degree, assigns lowest available colour || `colourings/` | ~330 colouring output files |

| **DSatur** | Greedy | O(V² + E) | Prioritizes vertices with most distinct neighbour colours (saturation) |

| **Simulated Annealing** | Metaheuristic | Configurable | Temperature-based probabilistic acceptance of worse solutions |### Performance Insights

| **Genetic Algorithm** | Evolutionary | O(P × G × V) | Population-based with crossover, mutation, and selection |

| **Tabu Search** | Metaheuristic | O(I × V × k) | TabuCol algorithm - iterative conflict repair with memory || Graph Family | Best Algorithm | Avg Ratio (colors/optimal) |

| **Exact Solver** | Branch-and-bound | Exponential | Guarantees optimal chromatic number ||--------------|----------------|---------------------------|

| anna, david, games, homer, huck, jean | All (tie) | 1.0 (optimal) |

### Tabu Search (TabuCol) - Details| fpsol, inithx, miles | DSatur | 1.0 (optimal) |

| DSJC | DSatur | 1.29 |

The **Tabu Search** algorithm is an industry-standard metaheuristic that was added to address the performance limitations of the Genetic Algorithm.| DSJR | Genetic | 1.02 |

| flat | Genetic | 1.78 |

**Strategy:**| le (Leighton) | DSatur | 1.46 |



1. Start with a random k-colouring (may have conflicts)---

2. Iteratively select a conflicting vertex and move it to the colour that minimizes conflicts

3. Mark the move (vertex, old_colour) as "tabu" for a tenure period to prevent cycling back## How to Use

4. Accept the best non-tabu move; allow tabu moves only if they achieve a new global best (aspiration criterion)

5. If zero conflicts achieved, decrease k and restart### Build

6. Stop when no feasible k-colouring found within iteration limit```bash

make all

**Key Parameters:**# Output: build/benchmark_runner

```

- `max_iterations`: Maximum iterations per k value (default: 10000 or 100×|V|)

- `tabu_tenure`: Number of iterations a move stays forbidden (default: 7 or |V|/10)### Run Single Algorithm

```bash

---make run-dsatur GRAPH=dimacs/myciel6.col

make run-genetic GRAPH=dimacs/myciel6.col

## Input/Output Formatsmake run-exact GRAPH=dimacs/myciel6.col

```

### Input (DIMACS `.col` format)

### Run All Benchmarks

```text```bash

c Comments start with 'c'make run-all-benchmarking

p edge 11 20          # Problem line: 11 vertices, 20 edges# Runs all algorithms on all graphs with timeouts (15s first pass, 30s retry)

e 1 2                 # Edge from vertex 1 to 2 (1-indexed)# Output: results/run_all_results.csv

e 1 4```

e 2 3

...### Animate Colouring

``````bash

python3 scripts/animate_coloring.py --graph myciel6 --algo dsatur

### Colouring Outputpython3 scripts/animate_coloring.py --graph myciel6 --algo tabu_search

python3 scripts/animate_coloring.py --graph myciel6 --all-algos

```text```

c colouring generated by benchmark framework

p edge 11 20---

v 1 1                 # Vertex 1 assigned colour 1

v 2 0                 # Vertex 2 assigned colour 0## Key Scripts

v 3 2

...| Script | Purpose |

```|--------|---------|

| `run_all_benchmarks.py` | Orchestrates batch runs with timeouts |

### Results CSV| `generate_graphs.py` | Generates synthetic graphs using NetworkX |

| `animate_coloring.py` | Visualizes colouring progression from snapshots |

```csv| `family_graphs.py` | Aggregates results by graph family |

algorithm,graph_name,vertices,edges,colors_used,known_optimal,runtime_ms,status

dsatur,myciel6,95,755,7,7,0.135,ok---

tabu_search,queen8_8,64,728,9,9,156.78,ok

genetic,DSJC125.5,125,3891,20,17,2340.56,ok## Technical Details

exact_solver,myciel3,11,20,4,4,0.045,ok

```- **Language**: C++20 with Python 3.8+ for orchestration

- **Build**: Makefile-based

### Snapshot Format- **Graph Representation**: Adjacency list (`std::vector<std::vector<int>>`)

- **Timing**: `std::chrono::high_resolution_clock`

Each line represents algorithm state at one iteration:

---

```text

-1 -1 -1 -1 -1 -1 0    # Step 1: only vertex 6 coloured## Algorithm Performance Notes

-1 -1 -1 -1 -1 1 0     # Step 2: vertex 5 gets colour 1

...### Most Disappointing: Genetic Algorithm

0 1 2 1 2 1 0          # Final colouringThe Genetic Algorithm was computationally expensive (taking up to 86 seconds for DSJC1000.5) without providing better solutions than DSatur. In some cases, it even timed out or produced worse results.

```

### Recommended Alternative: Tabu Search (TabuCol)

Legend:Tabu Search was implemented as a replacement for the underperforming Genetic/SA algorithms. It is the industry standard metaheuristic for graph colouring due to:

- **Efficiency**: No expensive population management

- `-1` = uncoloured vertex- **Effectiveness**: Memory-based escape from local optima

- `0, 1, 2, ...` = assigned colour number- **Proven track record**: Standard choice in DIMACS benchmarks



------



## Performance Results## Future Work



### Best Algorithm by Graph Family- [x] ~~Implement Tabu Search algorithm~~ (Completed)

- [ ] Benchmark Tabu Search against other algorithms

| Graph Family | Best Algorithm | Avg Ratio (colors/optimal) |- [ ] Add more graph families to benchmarks

|--------------|----------------|---------------------------|- [ ] Fine-tune Tabu Search parameters (tenure, iterations)

| anna, david, games, homer, huck, jean | All (tie) | 1.0 (optimal) |- [ ] Add parallel execution support

| fpsol, inithx, miles | DSatur | 1.0 (optimal) |- [ ] Consider hybrid approaches (e.g., Tabu + SA)

| DSJC | DSatur | 1.29 |
| DSJR | Genetic | 1.02 |
| flat | Genetic | 1.78 |
| le (Leighton) | DSatur | 1.46 |
| queen | DSatur | ~1.1 |
| mycielski | All | 1.0 (optimal on small) |

### Algorithm Performance Notes

**Most Reliable: DSatur**

- Consistently produces good results across all graph families
- Fast execution (sub-second for most graphs)
- Recommended as the default choice

**Best for Hard Instances: Tabu Search**

- Often matches or beats DSatur on difficult graphs
- Better at escaping local optima than greedy methods
- Industry standard for graph colouring competitions

**Most Disappointing: Genetic Algorithm**

- Computationally expensive (up to 86 seconds for DSJC1000.5)
- Rarely beats DSatur despite higher cost
- Sometimes produces worse results

---

## Technical Details

- **Language**: C++20 with Python 3.8+ for orchestration
- **Build System**: GNU Make
- **Graph Representation**: Adjacency list (`std::vector<std::vector<int>>`)
- **Timing**: `std::chrono::high_resolution_clock`
- **Visualization**: matplotlib + networkx

---

## Usage

For detailed usage instructions, see **[USAGE.md](USAGE.md)**.

### Quick Reference

```bash
# Build
make all

# Run single algorithm
make run-dsatur GRAPH=dimacs/myciel6.col
make run-tabu GRAPH=dimacs/queen8_8.col SNAPSHOTS=1

# Run all benchmarks
make run-all-benchmarking

# Animate
python3 tools/animate_coloring.py --graph myciel6 --algo dsatur
python3 tools/animate_coloring.py --graph myciel6 --all-algos

# Generate graphs
python3 tools/generate_graphs.py --seed 42
```

---

## Batch Benchmarking with `run_all_benchmarks.py`

The `tools/run_all_benchmarks.py` script orchestrates running all algorithms on all graphs with sophisticated timeout handling and result aggregation.

### Execution Order

Algorithms are run in this order (fast heuristics first, slow metaheuristics last):

1. **DSatur** - Greedy saturation-based (timeout: 60s)
2. **Welsh-Powell** - Greedy degree-based (timeout: 60s)
3. **Simulated Annealing** - Temperature-based metaheuristic (timeout: 120s)
4. **Tabu Search** - Memory-based metaheuristic (timeout: 120s)
5. **Genetic Algorithm** - Evolutionary approach (timeout: 180s)
6. **Exact Solver** - Branch-and-bound (timeout: 300s, optional, run last)

### Key Options

```bash
# Run on DIMACS only (no exact solver)
python3 tools/run_all_benchmarks.py --no-exact

# Run on generated graphs only
python3 tools/run_all_benchmarks.py --include-generated --graphs data/generated/*.col

# Custom output file for DIMACS results
python3 tools/run_all_benchmarks.py --no-exact -o dimacs_results.csv

# Custom output file for generated graph results
python3 tools/run_all_benchmarks.py --include-generated --graphs data/generated/*.col --no-exact -o generated_results.csv

# Set custom timeout for specific algorithm
python3 tools/run_all_benchmarks.py --algo-timeout genetic 300 --algo-timeout tabu_search 180

# Limit exact solver to small graphs
python3 tools/run_all_benchmarks.py --exact-max-vertices 100 --exact-timeout 60
```

### All CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--no-exact` | Skip exact_solver entirely | False |
| `--include-generated` | Include generated graphs | False |
| `--graphs PATH...` | Explicit graph files (overrides discovery) | None |
| `--output-file`, `-o` | Custom output CSV filename | `run_all_results.csv` |
| `--first-timeout` | Default first-pass timeout (seconds) | 150 |
| `--second-timeout` | Retry timeout for timed-out jobs | 300 |
| `--exact-timeout` | Timeout for exact_solver | 300 |
| `--exact-max-vertices` | Skip exact_solver on larger graphs | 500 |
| `--algo-timeout ALGO SEC` | Set timeout for specific algorithm | Per-algo defaults |

---

## Results Files Explained

### `results/results.csv`

**Purpose**: Individual/ad-hoc benchmark runs via Makefile targets.

**When Used**: When you run a single algorithm via:
```bash
make run-dsatur GRAPH=dimacs/myciel6.col
./build/benchmark_runner --algorithm dsatur --input data/dimacs/myciel6.col --results results/results.csv
```

**Schema**:
```csv
algorithm,graph_name,vertices,edges,colors_used,known_optimal,runtime_ms
dsatur,myciel6,95,755,7,7,0.135
```

**Note**: No `status` column - assumes successful completion.

### `results/run_all_results.csv`

**Purpose**: Batch benchmark results from `run_all_benchmarks.py`.

**When Used**: When running the batch orchestrator:
```bash
python3 tools/run_all_benchmarks.py --no-exact
```

**Schema** (includes status column):
```csv
algorithm,graph_name,vertices,edges,colors_used,known_optimal,runtime_ms,status
dsatur,myciel6,95,755,7,7,0.135,ok
tabu_search,DSJC1000.9,1000,449449,250,,120000,timeout(first-pass)
exact_solver,latin_square_10,900,307350,,,, skipped(too-large)
```

**Status Values**:
- `ok` - Completed successfully
- `ok(retry)` - Completed on second attempt
- `timeout(first-pass)` - Timed out, will retry
- `timeout>retry` - Timed out after retry
- `skipped(too-large)` - Graph too large for exact_solver
- `error` - Non-zero exit code

### Why Two Separate Files?

1. **Different Use Cases**:
   - `results.csv`: Quick single runs during development/debugging
   - `run_all_results.csv`: Comprehensive batch benchmarking with status tracking

2. **Different Schemas**:
   - Batch runs need `status` column to track timeouts/errors
   - Single runs assume success (or fail loudly)

3. **Separation of Concerns**:
   - Keep ad-hoc test results separate from comprehensive benchmark data
   - Allows running small tests without polluting main benchmark results

4. **Custom Output Files**:
   - Use `-o dimacs_results.csv` for DIMACS-only benchmarks
   - Use `-o generated_results.csv` for generated graph benchmarks
   - Keeps different dataset results organized

---

## Dataset Creation

### DIMACS Benchmark Graphs

The DIMACS graphs in `data/dimacs/` are standard benchmark instances from the DIMACS Graph Colouring Challenge. They were fetched using legacy scripts:

```bash
# Original fetch scripts (in legacy/)
python3 legacy/fetch_dimacs.py           # Download from DIMACS sources
python3 legacy/unzip_dimacs.py           # Extract archives
python3 legacy/convert_dimacs_binaries.py # Convert binary to text format
```

**Graph Families**:
- **Queen graphs** (`queen5_5.col` to `queen16_16.col`): n-queens conflict graphs
- **Mycielski graphs** (`myciel3.col` to `myciel7.col`): Triangle-free graphs with high chromatic number
- **DSJC graphs** (`DSJC125.1.col` to `DSJC1000.9.col`): Random graphs with varying density
- **Flat graphs** (`flat300_20_0.col` to `flat1000_76_0.col`): k-colourable graphs
- **Leighton graphs** (`le450_5a.col` to `le450_25d.col`): Register allocation instances
- **Real-world** (`anna.col`, `david.col`, `games120.col`, etc.): Various applications

**Metadata**: `data/metadata-dimacs.csv` contains known optimal chromatic numbers where available.

### Generated Graphs

Synthetic graphs are created using `tools/generate_graphs.py` with NetworkX:

```bash
# Generate all graph types
python3 tools/generate_graphs.py --seed 42 --target data/generated

# Generate specific types only
python3 tools/generate_graphs.py --types bipartite planar tree

# Regenerate existing graphs
python3 tools/generate_graphs.py --overwrite
```

**Graph Types Generated**:

| Type | Count | Size Range | Description |
|------|-------|------------|-------------|
| `bipartite` | 5 | 50-1000 | Random bipartite graphs (χ = 2) |
| `planar` | 5 | 50-500 | Random planar graphs (χ ≤ 4) |
| `tree` | 5 | 50-1000 | Random trees (χ = 2) |
| `grid` | 5 | 100-2500 | 2D grid graphs (χ = 2) |
| `erdos_renyi` | 10 | 100-2000 | Erdős-Rényi random graphs |
| `barabasi_albert` | 10 | 100-2000 | Scale-free networks |
| `watts_strogatz` | 10 | 100-1000 | Small-world networks |
| `complete` | 5 | 10-100 | Complete graphs (χ = n) |

**Metadata**: `data/metadata-generated.csv` tracks graph properties and generation parameters.

---

## Future Work

- [ ] Benchmark Tabu Search extensively against other algorithms
- [ ] Fine-tune Tabu Search parameters (tenure, iterations) per graph family
- [ ] Add parallel execution support for batch runs
- [ ] Implement hybrid approaches (e.g., DSatur initialization + Tabu refinement)
- [ ] Add more graph families to benchmarks
- [ ] Create automated parameter tuning
