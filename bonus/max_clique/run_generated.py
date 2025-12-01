#!/usr/bin/env python3
import os
import subprocess
import time
import csv
from pathlib import Path

# Paths
BONUS_DIR = Path(__file__).parent.resolve()
ROOT_DIR = BONUS_DIR.parent.parent
DATA_DIR = ROOT_DIR / "data" / "generated"
CPP_FILE = BONUS_DIR / "max_clique.cpp"
EXECUTABLE = BONUS_DIR / "max_clique"
RESULTS_FILE = BONUS_DIR / "results" / "generated.csv"

def compile_cpp():
    print("Compiling C++ code...")
    cmd = ["g++", "-O3", "-std=c++17", str(CPP_FILE), "-o", str(EXECUTABLE)]
    try:
        subprocess.run(cmd, check=True)
        print("Compilation successful.")
    except subprocess.CalledProcessError as e:
        print(f"Compilation failed: {e}")
        exit(1)

def get_graph_metadata(file_path):
    v, e = 0, 0
    try:
        with open(file_path, 'r') as f:
            for line in f:
                if line.startswith("p edge"):
                    parts = line.split()
                    if len(parts) >= 4:
                        v = int(parts[2])
                        e = int(parts[3])
                        break
    except Exception:
        pass
    return v, e

def run_benchmarks():
    if not DATA_DIR.exists():
        print(f"Data directory not found: {DATA_DIR}")
        return

    files = sorted(list(DATA_DIR.glob("*.col")))
    if not files:
        print("No .col files found in data directory.")
        return

    print(f"Found {len(files)} graphs. Starting benchmarks...")

    with open(RESULTS_FILE, 'w', newline='') as csvfile:
        fieldnames = ['graph_name', 'vertices', 'edges', 'max_clique_size', 'runtime_ms']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for file_path in files:
            graph_name = file_path.stem
            print(f"Processing {graph_name}...", end='', flush=True)
            
            v, e = get_graph_metadata(file_path)

            try:
                # Run the C++ executable
                # Using a timeout to prevent hanging on very large graphs if necessary
                # But Bron-Kerbosch can be slow, so we'll give it some time or no timeout for now
                # Let's add a reasonable timeout of 30s for now to be safe
                result = subprocess.run(
                    [str(EXECUTABLE), str(file_path)],
                    capture_output=True,
                    text=True,
                    timeout=30 
                )
                
                output = result.stdout
                lines = output.strip().split('\n')
                
                clique_size = 0
                runtime = 0
                
                for line in lines:
                    if line.startswith("Max Clique Size:"):
                        clique_size = int(line.split(":")[1].strip())
                    elif line.startswith("Time (ms):"):
                        runtime = int(line.split(":")[1].strip())

                writer.writerow({
                    'graph_name': graph_name,
                    'vertices': v,
                    'edges': e,
                    'max_clique_size': clique_size,
                    'runtime_ms': runtime
                })
                print(f" Done. Size: {clique_size}, Time: {runtime}ms")

            except subprocess.TimeoutExpired:
                print(" Timeout!")
                writer.writerow({
                    'graph_name': graph_name,
                    'vertices': v,
                    'edges': e,
                    'max_clique_size': "TIMEOUT",
                    'runtime_ms': ">30000"
                })
            except Exception as e:
                print(f" Error: {e}")
                writer.writerow({
                    'graph_name': graph_name,
                    'vertices': v,
                    'edges': e,
                    'max_clique_size': "ERROR",
                    'runtime_ms': "ERROR"
                })

    print(f"\nBenchmarks completed. Results saved to {RESULTS_FILE}")

if __name__ == "__main__":
    # compile_cpp()
    run_benchmarks()
