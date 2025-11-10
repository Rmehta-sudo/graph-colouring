#include "simulated_annealing.h"

#include <stdexcept>
#include <algorithm>
#include <cmath>
#include <limits>
#include <numeric>
#include <random>
#include <vector>
#include <fstream>

namespace {
// small helpers local to this translation unit
int count_conflicts(const graph_colouring::Graph &graph, const std::vector<int> &colours) {
	int conflicts = 0;
	const int n = graph.vertex_count;
	for (int u = 0; u < n; ++u) {
		const int cu = colours[u];
		for (int v : graph.adjacency_list[u]) {
			if (u < v && cu == colours[v]) ++conflicts;
		}
	}
	return conflicts;
}

int count_conflicts_local(const graph_colouring::Graph &graph, const std::vector<int> &colours, int vertex) {
	int conf = 0;
	const int n = graph.vertex_count;
	int c = colours[vertex];
	for (int nb : graph.adjacency_list[vertex]) {
		if (nb >= 0 && nb < n && colours[nb] == c) ++conf;
	}
	return conf;
}

int count_colour_usage(const std::vector<int> &colours) {
	int maxc = -1;
	for (int c : colours) maxc = std::max(maxc, c);
	return maxc >= 0 ? (maxc + 1) : 0;
}

// Greedy repair that respects palette_k (copied-in style from genetic helper but slimmed)
std::vector<int> greedy_repair_fixed_k(const graph_colouring::Graph &graph, const std::vector<int> &seed, int palette_k) {
	const int n = graph.vertex_count;
	std::vector<int> order(n);
	std::iota(order.begin(), order.end(), 0);
	std::sort(order.begin(), order.end(), [&](int a, int b) {
		return graph.adjacency_list[a].size() > graph.adjacency_list[b].size();
	});

	std::vector<int> colours(n, -1);
	std::vector<char> banned(palette_k, 0);

	for (int v : order) {
		std::fill(banned.begin(), banned.end(), 0);
		for (int nb : graph.adjacency_list[v]) {
			if (nb >= 0 && nb < n) {
				int c = colours[nb];
				if (c >= 0 && c < palette_k) banned[c] = 1;
			}
		}

		int preferred = (v < static_cast<int>(seed.size())) ? seed[v] : -1;
		if (preferred >= 0 && preferred < palette_k && !banned[preferred]) {
			colours[v] = preferred;
			continue;
		}

		int c = 0;
		while (c < palette_k && banned[c]) ++c;
		if (c < palette_k) {
			colours[v] = c;
		} else {
			// choose colour that minimises conflicts
			int best_c = 0;
			int best_conf = std::numeric_limits<int>::max();
			for (int tryc = 0; tryc < palette_k; ++tryc) {
				int conf = 0;
				for (int nb : graph.adjacency_list[v]) {
					if (nb >= 0 && nb < n && colours[nb] == tryc) ++conf;
				}
				if (conf < best_conf) {
					best_conf = conf;
					best_c = tryc;
				}
			}
			colours[v] = best_c;
		}
	}
	return colours;
}

int max_degree(const graph_colouring::Graph &graph) {
	int m = 0;
	for (const auto &nb : graph.adjacency_list) m = std::max<int>(m, static_cast<int>(nb.size()));
	return m;
}

} // anonymous namespace

namespace graph_colouring {

std::vector<int> colour_with_simulated_annealing(const Graph &graph) {
	// delegate to animated overload without recording steps
	std::vector<SAStep> steps;
	return colour_with_simulated_annealing(graph, false, steps);
}

std::vector<int> colour_with_simulated_annealing(const Graph &graph, bool animate, std::vector<SAStep> &steps) {
	const int n = graph.vertex_count;
	if (n == 0) return {};

	steps.clear();
	int step_counter = 1;

	std::mt19937 rng(std::random_device{}());

	// sensible starting palette: max_degree + 1 (upper bound)
	int start_palette = std::min(n, max_degree(graph) + 1);

	// track best valid solution found
	std::vector<int> best_valid_solution;
	int best_valid_k = std::numeric_limits<int>::max();

	// overall best (if no valid found) minimise conflicts then colours
	std::vector<int> best_overall;
	int best_overall_conflicts = std::numeric_limits<int>::max();
	int best_overall_k = std::numeric_limits<int>::max();

	// outer loop: try decreasing palette size
	for (int palette_k = start_palette; palette_k >= 1; --palette_k) {
		// initial random seed then greedy repair to respect palette_k
		std::vector<int> seed(n);
		std::uniform_int_distribution<int> colour_dist(0, std::max(0, palette_k - 1));
		for (int i = 0; i < n; ++i) seed[i] = colour_dist(rng);

		std::vector<int> colours = greedy_repair_fixed_k(graph, seed, palette_k);

		// record initial assignment if animating
		if (animate) {
			for (int v = 0; v < n; ++v) {
				steps.push_back(SAStep{step_counter++, v + 1, colours[v] + 1});
			}
		}

		int conflicts = count_conflicts(graph, colours);
		if (conflicts == 0) {
			best_valid_solution = colours;
			best_valid_k = std::min(best_valid_k, count_colour_usage(colours));
			continue;
		}

		// SA parameters
		const int iters = std::max(1000, n * 50);
		double T = 1.0;
		const double Tmin = 1e-4;
		const double alpha = std::pow(Tmin / T, 1.0 / static_cast<double>(iters));

		std::uniform_int_distribution<int> vertex_dist(0, n - 1);
		std::uniform_real_distribution<double> real01(0.0, 1.0);

		for (int iter = 0; iter < iters; ++iter) {
			int v = vertex_dist(rng);
			int oldc = colours[v];
			int newc = oldc;
			if (palette_k > 1) {
				int tries = 0;
				while (newc == oldc && ++tries < 10) newc = colour_dist(rng);
				if (newc == oldc) {
					for (int c = 0; c < palette_k; ++c) if (c != oldc) { newc = c; break; }
				}
			} else {
				newc = 0;
			}

			int old_local = count_conflicts_local(graph, colours, v);
			colours[v] = newc;
			int new_local = count_conflicts_local(graph, colours, v);
			int delta = new_local - old_local;

			bool accept = false;
			if (delta <= 0) accept = true;
			else if (real01(rng) < std::exp(-static_cast<double>(delta) / T)) accept = true;

			if (!accept) {
				colours[v] = oldc;
			} else {
				if (animate) steps.push_back(SAStep{step_counter++, v + 1, colours[v] + 1});
				conflicts += delta;
				if (conflicts < best_overall_conflicts || (conflicts == best_overall_conflicts && count_colour_usage(colours) < best_overall_k)) {
					best_overall = colours;
					best_overall_conflicts = conflicts;
					best_overall_k = count_colour_usage(colours);
				}
				if (conflicts == 0) break;
			}
			T *= alpha;
		}

		if (conflicts == 0) {
			best_valid_solution = colours;
			best_valid_k = std::min(best_valid_k, count_colour_usage(colours));
			continue;
		} else {
			if (!best_valid_solution.empty()) return best_valid_solution;
			if (!best_overall.empty()) return best_overall;
			return colours;
		}
	}

	if (!best_valid_solution.empty()) return best_valid_solution;
	if (!best_overall.empty()) return best_overall;
	return std::vector<int>(n, 0);

}

std::vector<int> colour_with_simulated_annealing_snapshots(const Graph &graph,
														   const std::string &snapshots_path) {
	std::vector<SAStep> steps;
	auto colours = colour_with_simulated_annealing(graph, true, steps);
	const int n = static_cast<int>(colours.size());
	std::ofstream out(snapshots_path);
	if (!out.is_open()) {
		throw std::runtime_error("Failed to open SA snapshots file: " + snapshots_path);
	}
	// Build frames from steps: start with all -1, then apply each step
	std::vector<int> frame(n, -1);
	for (const auto &s : steps) {
		int v0 = std::max(0, s.vertex - 1);
		if (v0 < n) frame[v0] = std::max(0, s.color - 1);
		for (int i = 0; i < n; ++i) {
			if (i) out << ' ';
			out << frame[i];
		}
		out << '\n';
	}
	// ensure final frame (in case no steps or incomplete)
	if (!steps.empty()) {
		for (int i = 0; i < n; ++i) {
			if (i) out << ' ';
			out << colours[i];
		}
		out << '\n';
	}
	return colours;
}

}  // namespace graph_colouring
