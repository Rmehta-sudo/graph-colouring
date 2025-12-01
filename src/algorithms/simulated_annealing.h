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

enum class SAMode {
	Default,
	Heavy,     // For dense/random graphs (DSJC, Flat, DSJR)
	Precision, // For structured/hard graphs (le450, latin_square)
	Speed      // For easy graphs (myciel, anna, david)
};

struct SAConfig {
	SAMode mode = SAMode::Default;
	// If mode is Default, these might be overridden by internal logic or used as base
	// If mode is custom, these can be used to tune specific parameters
	double initial_temperature = 1.0;
	int iteration_multiplier = 50; // iters = n * multiplier
	bool use_kempe_chains = false; // For Precision mode
	bool use_reheating = false;    // For Geometric graphs (optional future)
};

// Simulated annealing (two overloads)
// Basic call - no animation
std::vector<int> colour_with_simulated_annealing(const Graph &graph, const SAConfig &config = SAConfig{});

// Advanced call - can record steps when `animate==true`.
// `steps` will be filled with chronological assignment events (or left empty otherwise).
std::vector<int> colour_with_simulated_annealing(const Graph &graph, bool animate, std::vector<SAStep> &steps, const SAConfig &config = SAConfig{});

// SA with snapshots: writes the full colour vector after initial greedy repair
// and after each accepted move. Final frame is the final assignment.
std::vector<int> colour_with_simulated_annealing_snapshots(const Graph &graph,
														   const std::string &snapshots_path,
														   const SAConfig &config = SAConfig{});

}  // namespace graph_colouring
