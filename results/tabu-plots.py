import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import re

# -----------------------------
# 1. Load both CSVs
# -----------------------------
df_dimacs = pd.read_csv("run_on_dimacs.csv")
df_gen = pd.read_csv("run_on_generated.csv")

df_dimacs["source"] = "dimacs"
df_gen["source"] = "generated"

df = pd.concat([df_dimacs, df_gen], ignore_index=True)

# Convert numeric columns safely
for col in ["vertices", "edges", "colors_used", "known_optimal", "runtime_ms"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

# Status column: timeout flag
df["is_timeout"] = df["status"].astype(str).str.contains("timeout", case=False, na=False)

# -----------------------------
# 2. Add density
# -----------------------------
df["density"] = 2 * df["edges"] / (df["vertices"] * (df["vertices"] - 1))

# -----------------------------
# 3. Select only Tabu Search rows
# -----------------------------
tabu = df[df["algorithm"] == "tabu_search"].copy()

# -----------------------------
# 4. Output directory
# -----------------------------
OUT = "plots_tabu"
os.makedirs(OUT, exist_ok=True)

# ==========================================================
# PLOT 1 — Runtime vs Vertices
# ==========================================================
plt.figure(figsize=(8,6))
plt.scatter(tabu["vertices"], tabu["runtime_ms"], alpha=0.7)
plt.xlabel("Number of vertices")
plt.ylabel("Runtime (ms)")
plt.title("Tabu Search: Runtime vs Vertices")
plt.grid(True, linestyle="--", alpha=0.4)
plt.savefig(f"{OUT}/runtime_vs_vertices.png", dpi=200)
plt.close()

# ==========================================================
# PLOT 2 — Runtime vs Density
# ==========================================================
plt.figure(figsize=(8,6))
plt.scatter(tabu["density"], tabu["runtime_ms"], alpha=0.7, c="darkred")
plt.xlabel("Density")
plt.ylabel("Runtime (ms)")
plt.title("Tabu Search: Runtime vs Graph Density")
plt.grid(True, linestyle="--", alpha=0.4)
plt.savefig(f"{OUT}/runtime_vs_density.png", dpi=200)
plt.close()

# ==========================================================
# PLOT 3 — Colors Used vs Known Optimal
# ==========================================================
known = tabu[tabu["known_optimal"].notna()]

plt.figure(figsize=(7,7))
plt.scatter(known["known_optimal"], known["colors_used"], alpha=0.7)
mn, mx = known["known_optimal"].min(), known["known_optimal"].max()
plt.plot([mn, mx], [mn, mx], linestyle="--", color="gray")
plt.xlabel("Known optimal χ(G)")
plt.ylabel("Colors used by Tabu")
plt.title("Tabu Search: Colors vs Optimal")
plt.grid(True, linestyle="--", alpha=0.4)
plt.savefig(f"{OUT}/colors_vs_optimal.png", dpi=200)
plt.close()

# ==========================================================
# PLOT 4 — Optimality Ratio (colors/optimal)
# ==========================================================
known["opt_ratio"] = known["colors_used"] / known["known_optimal"]

plt.figure(figsize=(8,6))
plt.scatter(range(len(known)), known["opt_ratio"], alpha=0.7)
plt.axhline(1.0, color="gray", linestyle="--")
plt.xlabel("Instance index")
plt.ylabel("colors_used / optimal")
plt.title("Tabu Search: Optimality Ratio")
plt.grid(True, linestyle="--", alpha=0.4)
plt.savefig(f"{OUT}/optimality_ratio.png", dpi=200)
plt.close()

# ==========================================================
# PLOT 5 — Tabu vs DSATUR (colors comparison)
# ==========================================================
dsatur = df[df["algorithm"] == "dsatur"][["graph_name", "colors_used"]]
dsatur = dsatur.rename(columns={"colors_used": "dsatur_colors"})

merge_ds = tabu.merge(dsatur, on="graph_name", how="inner")

plt.figure(figsize=(7,7))
plt.scatter(merge_ds["dsatur_colors"], merge_ds["colors_used"], alpha=0.7)
mn = min(merge_ds["dsatur_colors"].min(), merge_ds["colors_used"].min())
mx = max(merge_ds["dsatur_colors"].max(), merge_ds["colors_used"].max())
plt.plot([mn, mx], [mn, mx], linestyle="--", color="gray")
plt.xlabel("DSATUR colors")
plt.ylabel("Tabu colors")
plt.title("Tabu vs DSATUR: Colors Used")
plt.grid(True, linestyle="--", alpha=0.4)
plt.savefig(f"{OUT}/tabu_vs_dsatur_colors.png", dpi=200)
plt.close()

# ==========================================================
# PLOT 6 — Tabu vs SA (colors comparison)
# ==========================================================
sa = df[df["algorithm"] == "simulated_annealing"][["graph_name", "colors_used"]]
sa = sa.rename(columns={"colors_used": "sa_colors"})

merge_sa = tabu.merge(sa, on="graph_name", how="inner")

plt.figure(figsize=(7,7))
plt.scatter(merge_sa["sa_colors"], merge_sa["colors_used"], alpha=0.7)
mn = min(merge_sa["sa_colors"].min(), merge_sa["colors_used"].min())
mx = max(merge_sa["sa_colors"].max(), merge_sa["colors_used"].max())
plt.plot([mn, mx], [mn, mx], linestyle="--", color="gray")
plt.xlabel("SA colors")
plt.ylabel("Tabu colors")
plt.title("Tabu vs SA: Colors Used")
plt.grid(True, linestyle="--", alpha=0.4)
plt.savefig(f"{OUT}/tabu_vs_sa_colors.png", dpi=200)
plt.close()

# ==========================================================
# FAMILY SUMMARY TABLE (optional)
# ==========================================================
def get_family(name):
    if "_" in name:
        parts = name.split("_")
        if parts[0].lower() in ("erdos","watts","barabasi"):
            return parts[0] + "_" + parts[1]
        return parts[0]
    return name

tabu["family"] = tabu["graph_name"].apply(get_family)

family_summary = tabu.groupby("family").agg(
    n=("graph_name","count"),
    mean_runtime=("runtime_ms","mean"),
    mean_colors=("colors_used","mean"),
    timeouts=("is_timeout","sum"),
).reset_index()

family_summary.to_csv(f"{OUT}/tabu_family_summary.csv", index=False)

print("All plots generated successfully into:", OUT)
