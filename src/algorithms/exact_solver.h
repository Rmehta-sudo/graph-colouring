/**
 * @file exact_solver.h
 * @brief Exact graph colouring solver using branch-and-bound.
 * 
 * Guarantees finding the optimal chromatic number χ(G) through exhaustive
 * search with pruning. Uses DSatur for upper bound initialization and
 * saturation-based vertex ordering for improved pruning.
 * 
 * WARNING: Exponential time complexity. Only practical for small graphs
 * (typically < 50 vertices depending on structure).
 * 
 * Time Complexity: O(k^V) worst case, with pruning typically much better.
 * Space Complexity: O(V) for recursion stack plus O(V + E) for graph.
 */

#pragma once

#include <vector>

#include "../utils.h"

namespace graph_colouring {

/**
 * @brief Finds an optimal colouring using branch-and-bound.
 * 
 * Algorithm:
 * 1. Compute upper bound using DSatur heuristic
 * 2. Recursively try all valid colourings with pruning:
 *    a. Select uncoloured vertex with maximum saturation
 *    b. Try existing colours that don't conflict
 *    c. Try new colour if it doesn't exceed current best
 *    d. Prune branches that cannot improve best solution
 * 3. Return optimal colouring (minimum colours used)
 * 
 * Progress reporting can be enabled via EXACT_PROGRESS_INTERVAL environment
 * variable (seconds between reports, default: 5.0, range: 0.05-600).
 * 
 * @param graph The input graph to colour.
 * @return std::vector<int> Optimal colour assignments where result[v] is the colour of vertex v (0-indexed).
 */
std::vector<int> colour_with_exact(const Graph &graph);

/**
 * @brief Exact solver with snapshots for visualization.
 * 
 * Writes the full colour vector each time an improved solution (lower k)
 * is found. Final line contains the optimal solution.
 * 
 * @param graph The input graph to colour.
 * @param snapshots_path Filesystem path for the snapshot output file.
 * @return std::vector<int> Optimal colour assignments (same as colour_with_exact).
 * @throws std::runtime_error If snapshot file cannot be opened.
 */
std::vector<int> colour_with_exact_snapshots(const Graph &graph, const std::string &snapshots_path);

}  // namespace graph_colouring
