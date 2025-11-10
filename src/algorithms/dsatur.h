#pragma once

#include <vector>
#include <string>

#include "../utils.h"

namespace graph_colouring {

// DSATUR heuristic colouring (to be implemented)
std::vector<int> colour_with_dsatur(const Graph &graph);

// DSATUR with per-iteration snapshots. When called, writes one line per
// vertex assignment to `snapshots_path`, containing the full colour vector
// (space-separated; uncoloured vertices are -1).
std::vector<int> colour_with_dsatur_snapshots(const Graph &graph, const std::string &snapshots_path);

}  // namespace graph_colouring
