


## Graph Coloring Project — Implementation Guidelines

> **Note:** This document describes the original specification. The actual implementation uses a unified `benchmark_runner` binary with CSV output instead of per-algorithm executables with JSON output.

### Current Implementation

The project uses a single `benchmark_runner` executable:

```bash
./build/benchmark_runner --algorithm <name> --input <graph.col> --output <result.col> --results <metrics.csv> [--save-snapshots]
```

**Supported Algorithms:**
- `welsh_powell` - Degree-ordered greedy
- `dsatur` - Saturation-based greedy  
- `simulated_annealing` - Temperature-based metaheuristic
- `genetic` - Evolutionary algorithm
- `tabu_search` - TabuCol metaheuristic
- `exact_solver` - Branch-and-bound exact

---

### Original Specification (Historical)

The original command format:

```bash
./<algorithm_name> --input <path_to_graph.col> --output <path_to_output.json> [--animate]
```

#### Example:

```bash
./dsatur --input graphs/sample.col --output results/dsatur_sample.json --animate
```

---

###  Input Format (`.col` file)

The input file follows the **DIMACS-style format**:

```
c some comments
c some comments 
...
p edge <num_vertices> <num_edges>
e <u1> <v1>
e <u2> <v2>
...
e <um> <vm>
```

Example:

```
c some comments
c some comments 
...
p edge 5 4
e 1 2
e 2 3
e 3 4
e 4 5
```

---

### Output Formats

#### Current: CSV Results

```csv
algorithm,graph_name,vertices,edges,colors_used,known_optimal,runtime_ms
dsatur,myciel6,95,755,7,7,0.234
```

#### Current: Colouring Output (`.col`)

```
c Coloring produced by dsatur
c Graph: myciel6.col
c Colors used: 7
v 1 1
v 2 2
v 3 1
...
```

#### Original Spec: JSON Output

```json
{
  "algorithm": "DSatur",
  "n": 5,
  "m": 4,
  "colors_used": 3,
  "runtime_ms": 1.27,
  "coloring": [1, 2, 3, 1, 2],
  "steps": []
}
```

---

### Animation / Snapshots

#### Current Implementation

Use `--save-snapshots` flag to generate snapshot files:

```bash
./build/benchmark_runner --algorithm dsatur --input graph.col --save-snapshots
```

Output: `output/snapshots/<algo>-<graph>-snapshots.txt`

Each line contains the complete colour assignment at that step:
```
-1 -1 -1 -1 -1
0 -1 -1 -1 -1
0 1 -1 -1 -1
0 1 0 -1 -1
...
```

Visualize with:
```bash
python3 tools/animate_coloring.py --graph myciel6 --algo dsatur
```

#### Original Spec: JSON Steps

```json
"steps": [
  {"step": 1, "vertex": 3, "color": 1},
  {"step": 2, "vertex": 1, "color": 2},
  {"step": 3, "vertex": 5, "color": 1}
]
```

---

### Timing

Use:

```cpp
auto start = chrono::high_resolution_clock::now();
// algorithm code
auto end = chrono::high_resolution_clock::now();
double runtime = chrono::duration<double, milli>(end - start).count();
```

---

### File Organization

| Component | Location |
|-----------|----------|
| Main runner | `src/benchmark_runner.cpp` |
| Algorithms | `src/algorithms/*.cpp` |
| I/O utilities | `src/io/*.cpp` |
| Python tools | `tools/*.py` |
| Bonus apps | `bonus/` |

### Algorithm Files

| Algorithm           | Header | Implementation |
| ------------------- | ------ | -------------- |
| Welsh–Powell        | `welsh_powell.h` | `welsh_powell.cpp` |
| DSatur              | `dsatur.h` | `dsatur.cpp` |
| Simulated Annealing | `simulated_annealing.h` | `simulated_annealing.cpp` |
| Exact Solver        | `exact_solver.h` | `exact_solver.cpp` |
| Genetic Algorithm   | `genetic.h` | `genetic.cpp` |
| Tabu Search         | `tabu.h` | `tabu.cpp` |

---

### Bonus Applications

#### Exam Scheduler (`bonus/exam_scheduler/`)

GUI application for conflict-free exam timetabling.

```bash
python3 bonus/exam_scheduler/exam_scheduler.py
```

#### Maximum Clique (`bonus/max_clique/`)

Bron-Kerbosch algorithm for finding maximum cliques.

```bash
cd bonus/max_clique
g++ -O3 -std=c++17 max_clique.cpp -o max_clique
./max_clique ../../data/dimacs/myciel6.col
```

---

### Rules

* Only **print errors** to `stderr`, never to `stdout`.
* All algorithm results go to **output files**, not the console.
* Handle invalid input gracefully (error message to `stderr` and exit).
* Avoid hardcoding paths.
* Use 1-based vertex indexing in DIMACS files, 0-based internally.

