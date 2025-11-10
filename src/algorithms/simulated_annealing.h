#pragma once

#include <vector>

#include "../utils.h"

namespace graph_colouring {

// Step record for animation/logging
struct SAStep {
	int step;   // 1-based step index
	int vertex; // 1-based vertex id
	int color;  // 1-based colour
};

// Simulated annealing (two overloads)
// Basic call - no animation
std::vector<int> colour_with_simulated_annealing(const Graph &graph);

// Advanced call - can record steps when `animate==true`.
// `steps` will be filled with chronological assignment events (or left empty otherwise).
std::vector<int> colour_with_simulated_annealing(const Graph &graph, bool animate, std::vector<SAStep> &steps);

// SA with snapshots: writes the full colour vector after initial greedy repair
// and after each accepted move. Final frame is the final assignment.
std::vector<int> colour_with_simulated_annealing_snapshots(const Graph &graph,
														   const std::string &snapshots_path);

}  // namespace graph_colouring
