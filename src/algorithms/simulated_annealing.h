/**
 * @file simulated_annealing.h
 * @brief Simulated Annealing (SA) metaheuristic for graph colouring.
 * 
 * Implements temperature-based probabilistic optimization that can escape
 * local optima by occasionally accepting worse solutions. Uses an exponential
 * cooling schedule and iterative palette reduction.
 * 
 * Time Complexity: O(I × V) where I=iterations (typically 50×V), V=vertices.
 * Space Complexity: O(V + E) for graph and colouring storage.
 */

#pragma once

#include <vector>

#include "../utils.h"

namespace graph_colouring {

/**
 * @struct SAStep
 * @brief Records a single vertex colouring step for animation/logging.
 */
struct SAStep {
	int step;   ///< 1-based step index in the algorithm
	int vertex; ///< 1-based vertex identifier
	int color;  ///< 1-based colour assignment
};

/**
 * @brief Colours a graph using Simulated Annealing (basic version).
 * 
 * Algorithm:
 * 1. For each palette size k (decreasing from upper bound):
 *    a. Initialize with greedy repair to k colours
 *    b. Run SA: randomly recolour vertices, accept based on temperature
 *    c. If zero conflicts achieved, record and try smaller k
 * 2. Return best valid colouring found
 * 
 * @param graph The input graph to colour.
 * @return std::vector<int> Colour assignments where result[v] is the colour of vertex v (0-indexed).
 */
std::vector<int> colour_with_simulated_annealing(const Graph &graph);

/**
 * @brief Colours a graph using Simulated Annealing with optional step recording.
 * 
 * @param graph The input graph to colour.
 * @param animate If true, records each accepted move to the steps vector.
 * @param steps Output vector filled with chronological assignment events (cleared first).
 * @return std::vector<int> Colour assignments (same as basic version).
 */
std::vector<int> colour_with_simulated_annealing(const Graph &graph, bool animate, std::vector<SAStep> &steps);

/**
 * @brief Simulated Annealing with per-move snapshots for visualization.
 * 
 * Writes the full colour vector after initial greedy repair and after each
 * accepted move. Final frame is the final colouring assignment.
 * 
 * @param graph The input graph to colour.
 * @param snapshots_path Filesystem path for the snapshot output file.
 * @return std::vector<int> Colour assignments (same as basic version).
 * @throws std::runtime_error If snapshot file cannot be opened.
 */
std::vector<int> colour_with_simulated_annealing_snapshots(const Graph &graph,
                                                           const std::string &snapshots_path);

}  // namespace graph_colouring
