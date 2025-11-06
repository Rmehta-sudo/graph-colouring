// DSATUR heuristic graph colouring (priority-queue based)
#include "dsatur.h"

#include <algorithm>
#include <set>
#include <unordered_set>
#include <vector>

namespace graph_colouring {

struct NodeInfo {
	int sat;    // saturation degree (distinct neighbour colours)
	int deg;    // degree in the uncoloured subgraph
	int v;      // vertex index (0-based)
};

struct MaxSatCmp {
	bool operator()(const NodeInfo &a, const NodeInfo &b) const {
		if (a.sat != b.sat) return a.sat > b.sat;       // higher saturation first
		if (a.deg != b.deg) return a.deg > b.deg;       // then higher degree
		return a.v < b.v;                                // then smaller vertex id
	}
};

std::vector<int> colour_with_dsatur(const Graph &graph) {
	const int n = graph.vertex_count;
	if (n == 0) return {};

	std::vector<int> colour(n, -1);
	std::vector<int> deg(n, 0);
	std::vector<int> sat(n, 0);
	std::vector<std::unordered_set<int>> nb_colours(n);

	for (int u = 0; u < n; ++u) deg[u] = static_cast<int>(graph.adjacency_list[u].size());

	std::set<NodeInfo, MaxSatCmp> Q;
	for (int u = 0; u < n; ++u) {
		Q.insert(NodeInfo{0, deg[u], u});
	}

	// temporary bitmap for used colours among neighbours
	std::vector<char> used;

	while (!Q.empty()) {
		// pick vertex with maximum saturation (tie by degree, then by id)
		int u = Q.begin()->v;
		Q.erase(Q.begin());

		// build used colour set among neighbours
		for (int nb : graph.adjacency_list[u]) {
			int c = colour[nb];
			if (c >= 0) {
				if (c >= static_cast<int>(used.size())) used.resize(c + 1, 0);
				used[c] = 1;
			}
		}

		// choose smallest non-negative colour not used
		int c = 0;
		while (c < static_cast<int>(used.size()) && used[c]) ++c;
		colour[u] = c;

		// reset used marks for next iteration
		for (int nb : graph.adjacency_list[u]) {
			int nc = colour[nb];
			if (nc >= 0 && nc < static_cast<int>(used.size())) used[nc] = 0;
		}

		// update neighbours still uncoloured
		for (int nb : graph.adjacency_list[u]) {
			if (colour[nb] == -1) {
				// erase old entry
				Q.erase(NodeInfo{sat[nb], deg[nb], nb});
				// update saturation if this colour is new for nb
				if (nb_colours[nb].insert(c).second) {
					++sat[nb];
				}
				// one of nb's uncoloured neighbours (u) is now coloured
				if (deg[nb] > 0) --deg[nb];
				// reinsert with updated key
				Q.insert(NodeInfo{sat[nb], deg[nb], nb});
			}
		}
	}

	return colour;
}

}  // namespace graph_colouring
