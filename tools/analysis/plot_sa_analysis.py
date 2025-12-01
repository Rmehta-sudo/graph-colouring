#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import sys

def parse_sa_results(file_path):
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return None
    
    df = pd.read_csv(file_path)
    
    # Extract base graph name and mode from "GraphName.col_Mode"
    # Assuming format: Name.col_Mode or Name_Mode
    def extract_info(row):
        name_part = row['graph_name']
        if '_' in name_part:
            # Split by last underscore
            parts = name_part.rsplit('_', 1)
            if len(parts) == 2:
                return parts[0], parts[1]
        return name_part, "Unknown"

    df[['base_graph', 'mode']] = df.apply(lambda x: pd.Series(extract_info(x)), axis=1)
    return df

def get_metadata_maps():
    metadata_path = "data/metadata-dimacs.csv"
    type_map = {}
    optimal_map = {}
    
    if os.path.exists(metadata_path):
        try:
            df = pd.read_csv(metadata_path)
            # Normalize names (remove .col for matching if needed, but keep original keys)
            # We'll store both "Name" and "Name.col" to be safe
            for _, row in df.iterrows():
                name = row['graph_name']
                gtype = row['graph_type']
                opt = row['known_optimal']
                
                type_map[name] = gtype
                if pd.notna(opt):
                    optimal_map[name] = float(opt)
                
                # Also map without .col if present
                if name.endswith('.col'):
                    short = name[:-4]
                    type_map[short] = gtype
                    if pd.notna(opt):
                        optimal_map[short] = float(opt)
                        
        except Exception as e:
            print(f"Error reading metadata: {e}")
            
    return type_map, optimal_map

def get_graph_type_map():
    t, _ = get_metadata_maps()
    return t

def get_type_label(name, type_map):
    # Try exact match
    if name in type_map:
        return f"{name}\n({type_map[name]})"
    # Try without .col
    if name.endswith('.col'):
        short = name[:-4]
        if short in type_map:
             return f"{name}\n({type_map[short]})"
    
    # Fallback heuristics
    if name.startswith('DSJC'): return f"{name}\n(Random)"
    if name.startswith('DSJR'): return f"{name}\n(Geometric)"
    if name.startswith('flat'): return f"{name}\n(Flat)"
    if name.startswith('le450'): return f"{name}\n(Leighton)"
    if name.startswith('latin'): return f"{name}\n(Latin Sq)"
    if name.startswith('school'): return f"{name}\n(School)"
    if name.startswith('myciel'): return f"{name}\n(Mycielski)"
    
    return name

def plot_parameter_comparison(df, output_dir):
    # Filter for relevant modes
    modes = ['Default', 'Heavy', 'Precision', 'Speed']
    df = df[df['mode'].isin(modes)]
    
    if df.empty:
        print("No data for parameter comparison.")
        return

    # Add graph type labels
    type_map = get_graph_type_map()
    df['label'] = df['base_graph'].apply(lambda x: get_type_label(x, type_map))

    # Pivot for easier calculation
    pivot_colors = df.pivot(index='base_graph', columns='mode', values='colors_used')
    pivot_time = df.pivot(index='base_graph', columns='mode', values='runtime_ms')
    
    # Calculate improvement over Default
    if 'Default' in pivot_colors.columns:
        for mode in modes:
            if mode != 'Default' and mode in pivot_colors.columns:
                pivot_colors[f'{mode}_imp'] = pivot_colors['Default'] - pivot_colors[mode]
                pivot_colors[f'{mode}_imp_pct'] = (pivot_colors[f'{mode}_imp'] / pivot_colors['Default']) * 100

    print("\nOptimization Improvement Analysis (Colors Used):")
    print(pivot_colors[[c for c in pivot_colors.columns if 'imp' in c]].describe())

    # Plot Colors
    plt.figure(figsize=(12, 8))
    sns.barplot(data=df, x='label', y='colors_used', hue='mode')
    plt.xticks(rotation=45, ha='right')
    plt.xlabel('Graph (Type)')
    plt.title('SA Parameter Optimization: Colors Used')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'sa_param_colors.png'))
    plt.close()

    # Plot Runtime
    plt.figure(figsize=(12, 8))
    sns.barplot(data=df, x='label', y='runtime_ms', hue='mode')
    plt.xticks(rotation=45, ha='right')
    plt.xlabel('Graph (Type)')
    plt.yscale('log')
    plt.title('SA Parameter Optimization: Runtime (ms)')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'sa_param_runtime.png'))
    plt.close()

def plot_general_sa_performance(results_dir, output_dir):
    dimacs_file = os.path.join(results_dir, "run_on_dimacs.csv")
    generated_file = os.path.join(results_dir, "run_on_generated.csv")
    
    dfs = []
    if os.path.exists(dimacs_file):
        dfs.append(pd.read_csv(dimacs_file))
    if os.path.exists(generated_file):
        dfs.append(pd.read_csv(generated_file))
        
    if not dfs:
        print("No results files found.")
        return

    df = pd.concat(dfs, ignore_index=True)
    
    # Filter for Simulated Annealing
    df_sa = df[df['algorithm'] == 'simulated_annealing'].copy()
    
    if df_sa.empty:
        print("No Simulated Annealing results found.")
        return

    # Define representative graphs to keep the plot clean
    # We pick ~2 from each major family to show diversity without clutter
    representative_graphs = [
        "DSJC125.1", "DSJC500.5", "DSJC1000.9", # Random
        "DSJR500.1c", # Geometric
        "flat300_28_0", "flat1000_50_0", # Flat
        "le450_15c", "le450_25a", # Leighton
        "latin_square_10", # Latin
        "school1", # School
        "myciel3", "myciel7", # Mycielski
        "queen11_11", # Queen
        "barabasi_albert_1193_7" # Generated example
    ]
    
    # Normalize names in df for matching (remove .col)
    df_sa['simple_name'] = df_sa['graph_name'].apply(lambda x: x[:-4] if x.endswith('.col') else x)
    
    # Filter
    df_rep = df_sa[df_sa['simple_name'].isin(representative_graphs)].copy()
    
    if df_rep.empty:
        print("Warning: No representative graphs found in results.")
        # Fallback to top 15
        df_rep = df_sa.head(15)
    
    # Sort for consistent plotting
    df_rep.sort_values('simple_name', inplace=True)

    # Plot 1: General Colors Used
    plt.figure(figsize=(12, 8))
    sns.barplot(data=df_rep, x='simple_name', y='colors_used', color='skyblue')
    plt.xticks(rotation=45, ha='right')
    plt.xlabel('Graph')
    plt.title('General SA Performance: Colors Used (Representative Subset)')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'sa_general_colors.png'))
    plt.close()

    # Plot 2: General Runtime
    plt.figure(figsize=(12, 8))
    sns.barplot(data=df_rep, x='simple_name', y='runtime_ms', color='salmon')
    plt.xticks(rotation=45, ha='right')
    plt.xlabel('Graph')
    plt.yscale('log')
    plt.title('General SA Performance: Runtime (Representative Subset)')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'sa_general_runtime.png'))
    plt.close()

def main():
    results_dir = "results"
    plots_dir = "plots"
    os.makedirs(plots_dir, exist_ok=True)
    
    sa_file = os.path.join(results_dir, "sa_optimization_results.csv")
    
    print("Loading SA Optimization Results...")
    df_sa = parse_sa_results(sa_file)
    
    if df_sa is not None:
        plot_parameter_comparison(df_sa, plots_dir)
    
    print("Generating General SA Performance Plots...")
    plot_general_sa_performance(results_dir, plots_dir)
    
    print(f"Plots saved to {plots_dir}")

if __name__ == "__main__":
    main()
