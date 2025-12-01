# Project Cleanup Plan for Presentation

This document outlines the recommended directory restructuring and file cleanup for a professional presentation.

---

## Current Issues

### 1. **Misplaced Files**
| File | Current Location | Problem |
|------|------------------|---------|
| `animate_coloring.py` | `scripts/` | Should be in dedicated tools folder |
| `run_all_benchmarks.py` | `scripts/` | Should be in dedicated tools folder |
| `family_graphs.py` | `results/` | Analysis script mixed with data |

### 2. **Inconsistent Naming**
| Current Name | Problem | Suggested Name |
|--------------|---------|----------------|
| `snapshots-colouring/` | British spelling + hyphen | `snapshots/` |
| `animation-videos/` | Empty folder, hyphen | `output/animations/` or delete |
| `fetch-dimacs-network-repo.py` | Hyphen in filename | `fetch_dimacs_network_repo.py` |
| `*-snnapshots.txt` | Typo "snnapshots" | `*-snapshots.txt` |

### 3. **Root Directory Clutter**
| File | Action |
|------|--------|
| `Cache_me_if_you_can_10.pdf` | Move to `docs/references/` |
| `marking-scheme.pdf` | Move to `docs/references/` |

### 4. **Redundant/Temporary Files**
| File/Folder | Location | Action |
|-------------|----------|--------|
| `tmp_run.csv` | `results/` | Delete (temporary) |
| `bin2asc.o` | `scripts/datasets/dimacs/` | Delete (compiled binary) |
| `col-b/` | `scripts/datasets/dimacs/` | Review if needed |
| `__pycache__/` | `scripts/` | Add to .gitignore |
| `venv/` | root | Should be in .gitignore |

### 5. **Poor Structure**
- `scripts/` contains both data (`datasets/`) and tools - these should be separate
- `info/` is vague - rename to `docs/`
- `support-files/` is vague - clarify purpose or merge

---

## Proposed New Structure

```
graph-colouring/
├── README.md                    # Main project README (move from info/)
├── Makefile
├── .gitignore                   # Update with proper exclusions
│
├── docs/                        # Documentation (renamed from info/)
│   ├── PROJECT_SUMMARY.md
│   ├── code-spec.md
│   ├── references/              # Academic papers, marking scheme
│   │   ├── Cache_me_if_you_can_10.pdf
│   │   ├── marking-scheme.pdf
│   │   └── Dataset_Metadata_AAD_citations.pdf
│   └── diagrams/                # For presentation diagrams if any
│
├── src/                         # C++ source (unchanged)
│   ├── benchmark_runner.cpp
│   ├── utils.h
│   ├── algorithms/
│   │   ├── dsatur.cpp/.h
│   │   ├── welsh_powell.cpp/.h
│   │   ├── genetic.cpp/.h
│   │   ├── simulated_annealing.cpp/.h
│   │   ├── exact_solver.cpp/.h
│   │   └── tabu.cpp/.h
│   └── io/
│       ├── graph_loader.cpp/.h
│       ├── graph_writer.cpp/.h
│       └── results_logger.cpp/.h
│
├── tools/                       # Python tools (NEW - split from scripts/)
│   ├── run_all_benchmarks.py
│   ├── animate_coloring.py
│   ├── generate_graphs.py
│   └── analysis/
│       └── family_graphs.py     # (moved from results/)
│
├── data/                        # All datasets (renamed from scripts/datasets/)
│   ├── dimacs/
│   │   └── *.col
│   ├── generated/
│   │   └── *.col
│   ├── network-repo/
│   ├── simple-tests/
│   ├── metadata-dimacs.csv
│   └── metadata-generated.csv
│
├── results/                     # Benchmark results
│   ├── colourings/
│   ├── results.csv
│   ├── run_all_results.csv
│   └── graph_family_best_analysis.csv
│
├── output/                      # Generated outputs (NEW)
│   ├── snapshots/               # (renamed from snapshots-colouring/)
│   └── animations/              # (renamed from animation-videos/)
│
├── build/                       # Build artifacts (in .gitignore)
│
└── legacy/                      # Old/unused scripts (or delete)
    ├── fetch_dimacs.py
    ├── fetch_dimacs_network_repo.py
    ├── unzip_dimacs.py
    ├── convert_dimacs_binaries.py
    └── support-files/
        ├── bin2asc.c
        ├── binformat.shar
        └── genbin.h
```

---

## Step-by-Step Commands

### Step 1: Create new directories
```bash
mkdir -p docs/references docs/diagrams
mkdir -p tools/analysis
mkdir -p data
mkdir -p output/snapshots output/animations
mkdir -p legacy
```

### Step 2: Move documentation
```bash
mv info/README.md ./README.md
mv info/PROJECT_SUMMARY.md docs/
mv info/code-spec.md docs/
mv Cache_me_if_you_can_10.pdf docs/references/
mv marking-scheme.pdf docs/references/
mv info/Dataset_Medadata_AAD_citations.pdf docs/references/Dataset_Metadata_AAD_citations.pdf
rmdir info
```

### Step 3: Reorganize scripts → tools + data
```bash
# Move tools
mv scripts/run_all_benchmarks.py tools/
mv scripts/animate_coloring.py tools/
mv scripts/generate_graphs.py tools/
mv results/family_graphs.py tools/analysis/

# Move datasets to data/
mv scripts/datasets/* data/
rmdir scripts/datasets

# Move legacy scripts
mv scripts/fetch_dimacs.py legacy/
mv scripts/fetch-dimacs-network-repo.py legacy/fetch_dimacs_network_repo.py
mv scripts/unzip-dimacs.py legacy/unzip_dimacs.py
mv scripts/convert_dimacs_binaries.py legacy/
mv support-files/* legacy/
rmdir support-files
rm -rf scripts/__pycache__
rmdir scripts
```

### Step 4: Rename and move output folders
```bash
# Fix snapshot folder and typo in filenames
mv snapshots-colouring output/snapshots
cd output/snapshots
for f in *-snnapshots.txt; do mv "$f" "${f/snnapshots/snapshots}"; done
cd ../..

# Move empty animation folder
rmdir animation-videos  # or mv animation-videos output/animations if has content
```

### Step 5: Clean up temporary/generated files
```bash
rm -f results/tmp_run.csv
rm -f data/dimacs/bin2asc.o
rm -rf data/dimacs/col-b  # if not needed
```

### Step 6: Update .gitignore
```
# Build artifacts
build/
*.o

# Python
__pycache__/
*.pyc
venv/
.venv/

# Temporary files
*.tmp
tmp_*.csv

# IDE
.vscode/
.idea/

# OS
.DS_Store
```

---

## Code Updates Required

After restructuring, update these file paths:

### 1. `Makefile`
Change dataset paths from `scripts/datasets/` to `data/`

### 2. `tools/run_all_benchmarks.py`
```python
# Update paths
DATASET_DIR = "../data"
RESULTS_DIR = "../results"
```

### 3. `tools/animate_coloring.py`
```python
# Update paths
SNAPSHOTS_DIR = "../output/snapshots"
OUTPUT_DIR = "../output/animations"
```

### 4. `tools/generate_graphs.py`
```python
# Update output path
OUTPUT_DIR = "../data/generated"
```

---

## Quick Wins (Do These First)

If short on time, prioritize these high-impact changes:

1. **Move README.md to root** - Essential for any project
2. **Rename `info/` → `docs/`** - More professional
3. **Move PDFs to `docs/references/`** - Clean root directory
4. **Delete `tmp_run.csv`** - Remove temporary files
5. **Fix `snnapshots` typo** - Looks unprofessional in demo

---

## Presentation Tips

1. **Clean root directory** matters most - panel sees this first
2. **Consistent naming** (all snake_case for Python, no hyphens)
3. **Clear separation**: source code vs tools vs data vs results
4. **No temporary files** in the repo
5. **Good README** at root level with build/run instructions
