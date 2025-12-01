import os
import subprocess
import csv
import time
from pathlib import Path

# Configuration
BENCHMARK_RUNNER = "./build/benchmark_runner"
DATASETS_DIR = "scripts/datasets/dimacs"
RESULTS_FILE = "results/sa_optimization_results.csv"

# Define the graph categories and their corresponding files
# You can add more files here
GRAPH_CATEGORIES = {
    "Random": ["DSJC125.1.col", "DSJC250.5.col"], # Heavy
    "Geometric": ["DSJR500.1c.col"], # Heavy (or custom) - r250.5.col missing
    "Flat": ["flat300_28_0.col"], # Heavy
    "Leighton": ["le450_15c.col"], # Precision
    "Latin": ["latin_square_10.col"], # Precision
    "Easy": ["myciel3.col", "anna.col", "david.col"] # Speed
}

# Define the configurations to test
CONFIGURATIONS = [
    {"name": "Default", "args": ["--sa-mode", "default"]},
    {"name": "Heavy", "args": ["--sa-mode", "heavy"]},
    {"name": "Precision", "args": ["--sa-mode", "precision"]},
    {"name": "Speed", "args": ["--sa-mode", "speed"]},
    # Custom experiment example
    # {"name": "Custom_HighTemp", "args": ["--sa-mode", "default", "--sa-initial-temp", "10.0", "--sa-iter-mult", "100"]}
]

def run_benchmark(graph_file, config_name, config_args):
    graph_path = os.path.join(DATASETS_DIR, graph_file)
    if not os.path.exists(graph_path):
        print(f"Warning: Graph file {graph_path} not found. Skipping.")
        return None

    cmd = [
        BENCHMARK_RUNNER,
        "--algorithm", "simulated_annealing",
        "--input", graph_path,
        "--results", RESULTS_FILE,
        "--graph-name", f"{graph_file}_{config_name}" # Tag graph name with config for CSV distinction
    ] + config_args

    print(f"Running {graph_file} with {config_name}...")
    try:
        start_time = time.time()
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        end_time = time.time()
        print(f"  -> Done in {end_time - start_time:.2f}s")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"  -> Error: {e.stderr}")
        return None

def main():
    # Ensure results directory exists
    os.makedirs(os.path.dirname(RESULTS_FILE), exist_ok=True)
    
    # Clear previous results or append? Let's clear for a fresh run
    if os.path.exists(RESULTS_FILE):
        os.remove(RESULTS_FILE)
        # Write header manually if needed, but the C++ runner appends. 
        # The C++ runner creates the file if it doesn't exist with header.
    
    print("Starting SA Optimization Benchmark...")
    
    for category, graphs in GRAPH_CATEGORIES.items():
        print(f"\n--- Category: {category} ---")
        for graph in graphs:
            for config in CONFIGURATIONS:
                run_benchmark(graph, config["name"], config["args"])

    print(f"\nAll benchmarks completed. Results saved to {RESULTS_FILE}")

if __name__ == "__main__":
    main()
