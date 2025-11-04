

##  Graph Coloring Project — Implementation Guidelines 
###  Command Format

Every algorithm executable must follow **this exact command-line format**:

```bash
./<algorithm_name> --input <path_to_graph.col> --output <path_to_output.json> [--animate]
```

#### Example:

```bash
./dsatur --input graphs/sample.col --output results/dsatur_sample.json --animate
```

---

###  Input Format (`.col` file)

The input file will follow the **DIMACS-style format**:

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

### Output Format (`.json`)

Each algorithm **must output a JSON file** in this structure:

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

#### Notes:

* `colors_used`: total number of unique colors used.
* `runtime_ms`: total runtime in milliseconds.
* `coloring`: color assigned to each vertex (1-indexed).
* `steps`: **optional**, used only if `--animate` flag is passed.

---

### 🎞️ Animation / Logging Mode (`--animate`)

If the `--animate` flag is provided, each algorithm should **record step-by-step color assignments**.

Example for `"steps"` field:

```json
"steps": [
  {"step": 1, "vertex": 3, "color": 1},
  {"step": 2, "vertex": 1, "color": 2},
  {"step": 3, "vertex": 5, "color": 1}
]
```

If `--animate` is **not** passed, `"steps"` must be an **empty array** (`[]`).

This will be used later for a Python visualizer to show coloring progression on small graphs.

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

###  File Naming Convention

| Algorithm           | Executable     | Source File        |
| ------------------- | -------------- | ------------------ |
| Welsh–Powell        | `welsh_powell` | `welsh_powell.cpp` |
| DSatur              | `dsatur`       | `dsatur.cpp`       |
| Simulated Annealing | `sim_anneal`   | `sim_anneal.cpp`   |
| Exact Solver        | `exact_dp`     | `exact_dp.cpp`     |
| Genetic Algorithm   | `genetic`      | `genetic.cpp`      |

---

###  Rules

* Only **print errors** to `stderr`, never to `stdout`.
* All algorithm results must go to the **output JSON file**, not the console.
* The code must handle invalid input gracefully (e.g., print an error message to `stderr` and exit).
* Avoid hardcoding paths.
* Use 1-based vertex indexing throughout.

