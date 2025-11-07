#include "exact_solver.h"
#include "dsatur.h"

#include <algorithm>
#include <limits>
#include <vector>

namespace graph_colouring {

namespace {

int count_colours(const std::vector<int> &colours) {
	int max_colour = -1;
	for (int c : colours) max_colour = std::max(max_colour, c);
	return max_colour >= 0 ? (max_colour + 1) : 0;
}

// Select next vertex via DSATUR criterion among uncoloured
int select_vertex(const Graph &g, const std::vector<int> &colours, int current_max_colour) {
	const int n = g.vertex_count;
	int best = -1;
	int best_sat = -1;
	int best_deg = -1;
	std::vector<char> used(static_cast<std::size_t>(std::max(1, current_max_colour + 1)), 0);

	for (int v = 0; v < n; ++v) {
		if (colours[v] != -1) continue;
		// compute saturation as number of distinct neighbour colours among [0..current_max_colour]
		std::fill(used.begin(), used.end(), 0);
		int sat = 0;
		for (int nb : g.adjacency_list[v]) {
			int c = colours[nb];
			if (c >= 0 && c <= current_max_colour && !used[c]) {
				used[c] = 1;
				++sat;
			}
		}
		int deg = static_cast<int>(g.adjacency_list[v].size());
		if (sat > best_sat || (sat == best_sat && deg > best_deg)) {
			best = v;
			best_sat = sat;
			best_deg = deg;
		}
	}
	return best;
}

void backtrack_exact(const Graph &g,
					 std::vector<int> &colours,
					 int coloured_count,
					 int current_max_colour,
					 int &best_k,
					 std::vector<int> &best_solution) {
	const int n = g.vertex_count;
	if (coloured_count == n) {
		const int used = current_max_colour + 1;
		if (used < best_k) {
			best_k = used;
			best_solution = colours;
		}
		return;
	}

	// Simple bound: if even with a new colour we cannot beat best_k, prune
	if (current_max_colour + 1 >= best_k) return;

	const int u = select_vertex(g, colours, current_max_colour);
	if (u == -1) return; // safety

	// Build banned colours from coloured neighbours
	std::vector<char> banned(static_cast<std::size_t>(std::max(1, current_max_colour + 1)), 0);
	for (int nb : g.adjacency_list[u]) {
		int c = colours[nb];
		if (c >= 0 && c <= current_max_colour) banned[c] = 1;
	}

	// Try existing colours first (0..current_max_colour)
	for (int c = 0; c <= current_max_colour; ++c) {
		if (banned[c]) continue;
		colours[u] = c;
		backtrack_exact(g, colours, coloured_count + 1, current_max_colour, best_k, best_solution);
		colours[u] = -1;
		// optional early exit: if we reached 1 colour (trivial), but skip as not realistic here
	}

	// Try a new colour if it can still improve best_k
	if (current_max_colour + 2 < best_k) {
		colours[u] = current_max_colour + 1;
		backtrack_exact(g, colours, coloured_count + 1, current_max_colour + 1, best_k, best_solution);
		colours[u] = -1;
	}
}

} // namespace

std::vector<int> colour_with_exact(const Graph &graph) {
	const int n = graph.vertex_count;
	if (n == 0) return {};

	// Use DSATUR to get a strong initial upper bound and seed solution
	std::vector<int> ub_solution = colour_with_dsatur(graph);
	int best_k = count_colours(ub_solution);
	if (best_k <= 1) return std::vector<int>(n, n ? 0 : -1);

	std::vector<int> colours(n, -1);
	std::vector<int> best_solution = ub_solution; // in case search prunes immediately

	// Kick off backtracking search
	backtrack_exact(graph, colours, /*coloured_count=*/0, /*current_max_colour=*/-1,
					best_k, best_solution);

	return best_solution;
}

}  // namespace graph_colouring
