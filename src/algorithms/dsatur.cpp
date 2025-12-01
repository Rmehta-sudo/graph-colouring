/**
 * @file dsatur.cpp
 * @brief Implementation of DSatur (Degree of Saturation) graph colouring algorithm.
 * 
 * DSatur is a greedy heuristic that maintains saturation degrees (count of
 * distinct colours among neighbours) and prioritizes vertices with highest
 * saturation. Uses a balanced BST (std::set) for efficient vertex selection.
 */

#include "dsatur.h"

#include <algorithm>
#include <fstream>
#include <set>
#include <stdexcept>
#include <unordered_set>
#include <vector>

namespace graph_colouring {

/**
 * @struct NodeInfo
 * @brief Stores vertex information for priority queue ordering in DSatur.
 */
struct NodeInfo {
	int sat;    ///< Saturation degree (number of distinct neighbour colours)
	int deg;    ///< Degree in the uncoloured subgraph
	int v;      ///< Vertex index (0-based)
};

/**
 * @struct MaxSatCmp
 * @brief Comparator for DSatur priority: max saturation, then max degree, then min vertex ID.
 */
struct MaxSatCmp {
	/**
	 * @brief Compares two NodeInfo objects for priority ordering.
	 * @param a First node.
	 * @param b Second node.
	 * @return true if a has higher priority than b.
	 */
	bool operator()(const NodeInfo &a, const NodeInfo &b) const {
		if (a.sat != b.sat) return a.sat > b.sat;       // higher saturation first
		if (a.deg != b.deg) return a.deg > b.deg;       // then higher degree
		return a.v < b.v;                                // then smaller vertex id
	}
};

/**
 * @brief Colours a graph using the DSatur heuristic algorithm.
 * 
 * Implementation uses a std::set with custom comparator for O(log V) vertex
 * selection and update operations. Total complexity is O(V² + E) in worst case
 * due to saturation updates.
 * 
 * @param graph The input graph to colour.
 * @return std::vector<int> Colour assignments (0-indexed).
 */
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

std::vector<int> colour_with_dsatur_snapshots(const Graph &graph, const std::string &snapshots_path) {
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

	std::vector<char> used;

	std::ofstream out(snapshots_path);
	if (!out.is_open()) {
		throw std::runtime_error("Failed to open DSATUR snapshots file: " + snapshots_path);
	}

	auto write_snapshot = [&](){
		for (int i = 0; i < n; ++i) {
			if (i) out << ' ';
			out << colour[i];
		}
		out << '\n';
	};

	while (!Q.empty()) {
		int u = Q.begin()->v;
		Q.erase(Q.begin());

		for (int nb : graph.adjacency_list[u]) {
			int c = colour[nb];
			if (c >= 0) {
				if (c >= static_cast<int>(used.size())) used.resize(c + 1, 0);
				used[c] = 1;
			}
		}

		int c = 0;
		while (c < static_cast<int>(used.size()) && used[c]) ++c;
		colour[u] = c;

		for (int nb : graph.adjacency_list[u]) {
			int nc = colour[nb];
			if (nc >= 0 && nc < static_cast<int>(used.size())) used[nc] = 0;
		}

		for (int nb : graph.adjacency_list[u]) {
			if (colour[nb] == -1) {
				Q.erase(NodeInfo{sat[nb], deg[nb], nb});
				if (nb_colours[nb].insert(c).second) {
					++sat[nb];
				}
				if (deg[nb] > 0) --deg[nb];
				Q.insert(NodeInfo{sat[nb], deg[nb], nb});
			}
		}

		write_snapshot();
	}

	return colour;
}

}  // namespace graph_colouring