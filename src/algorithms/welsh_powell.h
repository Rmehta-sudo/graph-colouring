/**
 * @file welsh_powell.h
 * @brief Welsh-Powell greedy graph colouring algorithm.
 * 
 * Welsh-Powell is a simple greedy heuristic that orders vertices by degree
 * (highest first) and assigns the smallest available colour. Fast but may
 * use more colours than DSatur on many graphs.
 * 
 * Time Complexity: O(V log V + E) for sorting and colour assignment.
 * Space Complexity: O(V + E) for adjacency list and auxiliary structures.
 */

#pragma once

#include <vector>
#include <string>

#include "../utils.h"

namespace graph_colouring {

/**
 * @brief Colours a graph using the Welsh-Powell greedy algorithm.
 * 
 * Algorithm:
 * 1. Sort vertices by degree in descending order
 * 2. For each colour class:
 *    a. Assign current colour to the first uncoloured vertex
 *    b. Assign same colour to subsequent uncoloured vertices if no conflict
 * 3. Repeat with next colour until all vertices are coloured
 * 
 * @param graph The input graph to colour.
 * @return std::vector<int> Colour assignments where result[v] is the colour of vertex v (0-indexed).
 *                          Returns empty vector if graph has no vertices.
 */
std::vector<int> colour_with_welsh_powell(const Graph &graph);

/**
 * @brief Welsh-Powell with per-assignment snapshots for visualization.
 * 
 * Writes one line per vertex colouring to the snapshots file. Each line contains
 * the full colour vector (space-separated), where -1 indicates uncoloured vertices.
 * 
 * @param graph The input graph to colour.
 * @param snapshots_path Filesystem path for the snapshot output file.
 * @return std::vector<int> Colour assignments (same as colour_with_welsh_powell).
 * @throws std::runtime_error If snapshot file cannot be opened.
 */
std::vector<int> colour_with_welsh_powell_snapshots(const Graph &graph, const std::string &snapshots_path);

}  // namespace graph_colouring
