/**
 * @file dsatur.h
 * @brief DSatur (Degree of Saturation) graph colouring algorithm.
 * 
 * DSatur is a greedy heuristic that prioritizes vertices based on their
 * saturation degree (number of distinct colours among neighbours). It often
 * produces near-optimal colourings and is the recommended general-purpose algorithm.
 * 
 * Time Complexity: O(V² + E) using priority queue with saturation updates.
 * Space Complexity: O(V + E) for adjacency list and auxiliary structures.
 */

#pragma once

#include <vector>
#include <string>

#include "../utils.h"

namespace graph_colouring {

/**
 * @brief Colours a graph using the DSatur heuristic algorithm.
 * 
 * Algorithm:
 * 1. Initialize all vertices as uncoloured with saturation = 0
 * 2. Repeat until all vertices are coloured:
 *    a. Select vertex with maximum saturation (ties broken by degree, then ID)
 *    b. Assign the smallest colour not used by any neighbour
 *    c. Update saturation of uncoloured neighbours
 * 
 * @param graph The input graph to colour.
 * @return std::vector<int> Colour assignments where result[v] is the colour of vertex v (0-indexed).
 *                          Returns empty vector if graph has no vertices.
 */
std::vector<int> colour_with_dsatur(const Graph &graph);

/**
 * @brief DSatur with per-iteration snapshots for visualization.
 * 
 * Writes one line per vertex assignment to the snapshots file. Each line contains
 * the full colour vector (space-separated), where -1 indicates uncoloured vertices.
 * 
 * @param graph The input graph to colour.
 * @param snapshots_path Filesystem path for the snapshot output file.
 * @return std::vector<int> Colour assignments (same as colour_with_dsatur).
 * @throws std::runtime_error If snapshot file cannot be opened.
 */
std::vector<int> colour_with_dsatur_snapshots(const Graph &graph, const std::string &snapshots_path);

}  // namespace graph_colouring
