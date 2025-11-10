#pragma once

#include <vector>
#include <string>

#include "../utils.h"

namespace graph_colouring {

// Welsh-Powell greedy colouring (to be implemented)
std::vector<int> colour_with_welsh_powell(const Graph &graph);

// Welsh-Powell with snapshots: after each colour class assignment phase,
// writes a line containing the full colour vector (space-separated; -1 for uncoloured)
// to the provided `snapshots_path`.
std::vector<int> colour_with_welsh_powell_snapshots(const Graph &graph, const std::string &snapshots_path);

}  // namespace graph_colouring
