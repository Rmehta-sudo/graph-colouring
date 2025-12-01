import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Set style
sns.set_theme(style="whitegrid")
plt.rcParams.update({'figure.figsize': (10, 6)})

# Load data
RESULTS_FILE = "results/sa_optimization_results.csv"
if not os.path.exists(RESULTS_FILE):
    print(f"Error: {RESULTS_FILE} not found.")
    exit(1)

df = pd.read_csv(RESULTS_FILE)

# Extract base graph name and mode
# Format is "GraphName.col_Mode"
def parse_mode(name):
    parts = name.split('_')
    return parts[-1]

def parse_graph(name):
    parts = name.split('_')
    return "_".join(parts[:-1])

df['Mode'] = df['graph_name'].apply(parse_mode)
df['Graph'] = df['graph_name'].apply(parse_graph)

# 1. Colors Used Comparison (Bar Chart)
plt.figure(figsize=(12, 6))
sns.barplot(data=df, x='Graph', y='colors_used', hue='Mode', palette='viridis')
plt.title('Colors Used by SA Configuration per Graph')
plt.xticks(rotation=45, ha='right')
plt.ylabel('Number of Colors (Lower is Better)')
plt.tight_layout()
plt.savefig('plots/sa_colors_comparison.png')
print("Generated plots/sa_colors_comparison.png")

# 2. Runtime Comparison (Log Scale Bar Chart)
plt.figure(figsize=(12, 6))
sns.barplot(data=df, x='Graph', y='runtime_ms', hue='Mode', palette='magma')
plt.title('Runtime by SA Configuration per Graph (Log Scale)')
plt.yscale('log')
plt.xticks(rotation=45, ha='right')
plt.ylabel('Runtime (ms) - Log Scale')
plt.tight_layout()
plt.savefig('plots/sa_runtime_comparison.png')
print("Generated plots/sa_runtime_comparison.png")

# 3. Efficiency Scatter Plot (Colors vs Time)
plt.figure(figsize=(10, 6))
sns.scatterplot(data=df, x='runtime_ms', y='colors_used', hue='Mode', style='Graph', s=100, palette='deep')
plt.xscale('log')
plt.title('Efficiency Trade-off: Quality vs Speed')
plt.xlabel('Runtime (ms) - Log Scale')
plt.ylabel('Colors Used')
plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.savefig('plots/sa_efficiency_scatter.png')
print("Generated plots/sa_efficiency_scatter.png")
