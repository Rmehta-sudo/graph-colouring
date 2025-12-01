#pragma once

#include <vector>
#include <string>

#include "../utils.h"

namespace graph_colouring {

// TabuCol: Tabu Search metaheuristic for graph colouring
// Starts with a (possibly conflicting) random k-colouring and iteratively
// repairs conflicts. Uses a tabu list to prevent cycling back to recent moves.
// Decreases k until no feasible solution is found.
std::vector<int> colour_with_tabu(const Graph &graph);

// TabuCol with configurable parameters
// - max_iterations: maximum iterations per k value (default: 10000)
// - tabu_tenure: number of iterations a move stays tabu (default: 7)
std::vector<int> colour_with_tabu(const Graph &graph, int max_iterations, int tabu_tenure);

// TabuCol with per-iteration snapshots. Writes the colour vector after each
// move that improves the solution (reduces conflicts or colours used).
// Final line is the best solution achieved.
std::vector<int> colour_with_tabu_snapshots(const Graph &graph, const std::string &snapshots_path);

}  // namespace graph_colouring
