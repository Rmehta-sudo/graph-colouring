/**
 * @file tabu.h
 * @brief TabuCol: Tabu Search metaheuristic for graph colouring.
 * 
 * Implements the industry-standard TabuCol algorithm that iteratively repairs
 * conflicts while using a tabu list to prevent cycling. Often achieves the
 * best results among metaheuristics for difficult instances.
 * 
 * Strategy:
 * 1. Start with a random k-colouring (may have conflicts)
 * 2. Iteratively move conflicting vertices to conflict-minimizing colours
 * 3. Mark recent moves as "tabu" to prevent cycling back
 * 4. Use aspiration criterion: allow tabu moves if they achieve new global best
 * 5. Decrease k when valid colouring found; stop when no feasible k-colouring found
 * 
 * Time Complexity: O(I × V × k) where I=iterations, V=vertices, k=colours.
 * Space Complexity: O(V × k) for tabu list plus O(V + E) for graph.
 */

#pragma once

#include <vector>
#include <string>

#include "../utils.h"

namespace graph_colouring {

/**
 * @brief Colours a graph using TabuCol with default parameters.
 * 
 * Uses max_iterations = max(10000, V×100) and tabu_tenure = max(7, V/10).
 * 
 * @param graph The input graph to colour.
 * @return std::vector<int> Colour assignments where result[v] is the colour of vertex v (0-indexed).
 */
std::vector<int> colour_with_tabu(const Graph &graph);

/**
 * @brief Colours a graph using TabuCol with configurable parameters.
 * 
 * @param graph The input graph to colour.
 * @param max_iterations Maximum iterations per palette size k.
 * @param tabu_tenure Number of iterations a move (vertex, colour) remains forbidden.
 * @return std::vector<int> Colour assignments where result[v] is the colour of vertex v (0-indexed).
 */
std::vector<int> colour_with_tabu(const Graph &graph, int max_iterations, int tabu_tenure);

/**
 * @brief TabuCol with per-improvement snapshots for visualization.
 * 
 * Writes the colour vector after each move that improves the solution
 * (reduces conflicts or achieves smaller k). Final line is the best solution.
 * 
 * @param graph The input graph to colour.
 * @param snapshots_path Filesystem path for the snapshot output file.
 * @return std::vector<int> Colour assignments (same as colour_with_tabu).
 * @throws std::runtime_error If snapshot file cannot be opened.
 */
std::vector<int> colour_with_tabu_snapshots(const Graph &graph, const std::string &snapshots_path);

}  // namespace graph_colouring
