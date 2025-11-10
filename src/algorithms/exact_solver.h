#pragma once

#include <vector>

#include "../utils.h"

namespace graph_colouring {

// Exact solver (e.g., branch-and-bound) placeholder
std::vector<int> colour_with_exact(const Graph &graph);

// Exact solver with snapshots: writes full colour vector each time an improved
// solution (lower k) is found and optionally at significant recursion events.
// To limit file size, only improvements plus final best are written.
std::vector<int> colour_with_exact_snapshots(const Graph &graph, const std::string &snapshots_path);

}  // namespace graph_colouring
