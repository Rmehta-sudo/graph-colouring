#!/usr/bin/env python3
"""Individual graph analysis and lightweight summaries.

Usage:
  python3 individual-graphs.py [run_all_results.csv]

If no path provided, searches ../results/run_all_results.csv relative to this script.
Optional analyses (Friedman + posthoc) run only if scipy & scikit-posthocs installed.
"""
from __future__ import annotations
import sys, os
from pathlib import Path
import pandas as pd
import numpy as np

# Optional heavy deps
try:
    import matplotlib.pyplot as plt
except Exception:
    plt = None
try:
    from scipy.stats import friedmanchisquare
except Exception:
    friedmanchisquare = None
try:
    import scikit_posthocs as sp
except Exception:
    sp = None

def locate_csv(arg: str | None) -> Path:
    if arg:
        p = Path(arg)
        if p.exists():
            return p
        raise SystemExit(f"CSV not found: {p}")
    # default search relative to repo layout
    default = Path(__file__).resolve().parents[1] / "results" / "run_all_results.csv"
    if default.exists():
        return default
    raise SystemExit("run_all_results.csv not found (pass path explicitly)")

csv_path = locate_csv(sys.argv[1] if len(sys.argv) > 1 else None)
df = pd.read_csv(csv_path)

required = ["algorithm","graph_name","vertices","edges","colors_used","known_optimal","runtime_ms","status"]
missing = [c for c in required if c not in df.columns]
if missing:
    raise SystemExit(f"Missing columns in input: {missing}")

for c in ["vertices","edges","colors_used","known_optimal","runtime_ms"]:
    df[c] = pd.to_numeric(df[c], errors="coerce")

df = df[df["status"].astype(str).str.startswith("ok")]
df = df.dropna(subset=["colors_used","known_optimal"])
df = df[df["known_optimal"] > 0]
if df.empty:
    raise SystemExit("No valid rows after filtering.")

df["ratio_to_optimal"] = df["colors_used"] / df["known_optimal"]
df["runtime_s"] = df["runtime_ms"] / 1000.0

# Per-graph winners (lowest colors_used; tie => all winners)
winner_rows = []
for gname, g in df.groupby("graph_name"):
    minc = g["colors_used"].min()
    winners = sorted(g.loc[g["colors_used"] == minc, "algorithm"].unique())
    winner_rows.append({"graph_name": gname, "min_colors": minc, "winners": ",".join(winners)})
win_df = pd.DataFrame(winner_rows)
win_df.to_csv("graph_winners.csv", index=False)

# Ranking (ratio then runtime)
rank_df = df.sort_values(["graph_name","ratio_to_optimal","runtime_s"]).copy()
rank_df["rank"] = rank_df.groupby("graph_name").cumcount() + 1
best = rank_df[rank_df["rank"] == 1][["graph_name","algorithm","colors_used","known_optimal","ratio_to_optimal","runtime_s"]]
best = best.rename(columns={"algorithm":"best_algorithm"})
best.to_csv("individual_graph_best.csv", index=False)
rank_df.to_csv("individual_graph_full.csv", index=False)

print("Top 15 graph winners:")
print(best.head(15).to_string(index=False))

# Algorithm summary
alg_summary = rank_df.groupby("algorithm").agg(
    graphs=("graph_name","nunique"),
    avg_ratio=("ratio_to_optimal","mean"),
    med_ratio=("ratio_to_optimal","median"),
    max_ratio=("ratio_to_optimal","max"),
    avg_runtime_ms=("runtime_ms","mean"),
).sort_values("avg_ratio")
alg_summary.to_csv("algorithm_summary_individual.csv")
print("\nAlgorithm summary (first lines):")
print(alg_summary.head().to_string())

# Optional plots if matplotlib available
if plt:
    os.makedirs("plots", exist_ok=True)
    # Ratio distribution per algorithm
    plt.figure(figsize=(8,5))
    for alg, g in rank_df.groupby("algorithm"):
        plt.scatter([alg]*len(g), g["ratio_to_optimal"], alpha=0.6)
    plt.ylabel("ratio_to_optimal")
    plt.title("Ratio by algorithm")
    plt.tight_layout()
    plt.savefig("plots/ratio_scatter_individual.png")
    plt.close()
else:
    print("matplotlib not available; skipping plots.")

# Friedman test (optional)
pivot = rank_df.pivot_table(index="graph_name", columns="algorithm", values="colors_used")
complete = pivot.dropna()
alg_names = complete.columns.tolist()
if friedmanchisquare and complete.shape[0] >= 10 and len(alg_names) >= 2:
    stat, p = friedmanchisquare(*[complete[c] for c in alg_names])
    print(f"\nFriedman test: chi2={stat:.3f} p={p:.4g} (n={complete.shape[0]})")
    if p < 0.05 and sp is not None:
        post = sp.posthoc_nemenyi_friedman(complete.values)
        post_df = pd.DataFrame(post, index=alg_names, columns=alg_names)
        post_df.to_csv("posthoc_nemenyi_individual.csv")
        print("Posthoc Nemenyi saved to posthoc_nemenyi_individual.csv")
    elif p < 0.05:
        print("Significant differences, but scikit-posthocs not installed for posthoc analysis.")
else:
    print("\nFriedman test skipped (insufficient data or scipy missing).")

print("\nOutputs written:")
print(" - graph_winners.csv")
print(" - individual_graph_best.csv")
print(" - individual_graph_full.csv")
print(" - algorithm_summary_individual.csv")
if plt:
    print(" - plots/ratio_scatter_individual.png")
if friedmanchisquare and complete.shape[0] >= 10 and len(alg_names) >= 2:
    print(" - posthoc_nemenyi_individual.csv (if p<0.05 and lib available)")
