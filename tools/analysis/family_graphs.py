#!/usr/bin/env python3
"""Family-level aggregate analysis for colouring runs.

Reads run_all_results.csv and produces:
  - graph_family_summary.csv (per family + algorithm metrics)
  - graph_family_best_analysis.csv (adds best_algo per family)

Families are derived from the leading alphabetical prefix of graph_name.
Only successful runs (status starts with 'ok') and rows with non-zero known_optimal are used.
"""
from __future__ import annotations
import pandas as pd
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "run_all_results.csv"
if not DATA.exists():
    raise SystemExit(f"Input not found: {DATA}. Run batch benchmarking first.")

df = pd.read_csv(DATA)
# Coerce numeric columns to numeric, preserve NaN on errors
for col in ("vertices","edges","colors_used","known_optimal","runtime_ms"):
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")
df = df[df["status"].str.startswith("ok")]
df = df.dropna(subset=["colors_used", "known_optimal"])  # require both
df = df[df["known_optimal"] > 0]

df["family"] = df["graph_name"].str.extract(r"^([A-Za-z]+)")
df["color_ratio"] = df["colors_used"] / df["known_optimal"].replace(0, np.nan)
df["runtime_s"] = df["runtime_ms"] / 1000.0

summary = (
    df.groupby(["family", "algorithm"], dropna=True)
      .agg(
          graphs=("graph_name", "count"),
          avg_vertices=("vertices", "mean"),
          avg_edges=("edges", "mean"),
          avg_colors=("colors_used", "mean"),
          avg_optimal=("known_optimal", "mean"),
          avg_ratio=("color_ratio", "mean"),
          max_ratio=("color_ratio", "max"),
          avg_runtime_s=("runtime_s", "mean"),
      ).reset_index()
)

if summary.empty:
    raise SystemExit("No data after filtering; cannot build family summary.")

best_algos = (
    summary.loc[summary.groupby("family")["avg_ratio"].idxmin(), ["family", "algorithm", "avg_ratio"]]
            .rename(columns={"algorithm": "best_algo", "avg_ratio": "best_avg_ratio"})
)

merged = summary.merge(best_algos, on="family", how="left")

# Format numeric columns to 5 decimal places for CSV output
for col in ["avg_vertices", "avg_edges", "avg_colors", "avg_optimal", "avg_ratio", "max_ratio", "avg_runtime_s", "best_avg_ratio"]:
    if col in summary.columns:
        summary[col] = summary[col].round(5)
    if col in merged.columns:
        merged[col] = merged[col].round(5)

for family, subset in summary.groupby("family"):
    print(f"\n=== {family} Family ===")
    display_cols = ["algorithm", "graphs", "avg_ratio", "max_ratio", "avg_runtime_s"]
    subset_display = subset[display_cols].copy()
    for col in ["avg_ratio", "max_ratio", "avg_runtime_s"]:
        subset_display[col] = subset_display[col].apply(lambda x: f"{x:.5f}")
    print(subset_display.to_string(index=False))
    best = best_algos[best_algos["family"] == family]["best_algo"].values[0]
    print(f"Best algorithm: {best}")

print("\n=== Overall Algorithm Comparison ===")
overall = (
    df.groupby("algorithm")
      .agg(
          total_graphs=("graph_name", "count"),
          mean_ratio=("color_ratio", "mean"),
          mean_runtime=("runtime_s", "mean"),
          max_ratio=("color_ratio", "max"),
      ).sort_values("mean_ratio")
)
overall_display = overall.copy()
for col in ["mean_ratio", "mean_runtime", "max_ratio"]:
    overall_display[col] = overall_display[col].apply(lambda x: f"{x:.5f}")
print(overall_display.to_string())

merged.to_csv(ROOT / "graph_family_best_analysis.csv", index=False)
print("\nSaved: graph_family_best_analysis.csv")
