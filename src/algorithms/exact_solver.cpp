#include "exact_solver.h"
#include "dsatur.h"

#include <algorithm>
#include <chrono>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <vector>
#include <fstream>
#include <functional>

namespace graph_colouring {
namespace {

int count_colours(const std::vector<int> &colours) {
	int max_colour = -1;
	for (int c : colours) max_colour = std::max(max_colour, c);
	return max_colour >= 0 ? (max_colour + 1) : 0;
}

int select_vertex(const Graph &g, const std::vector<int> &colours, int current_max_colour) {
	const int n = g.vertex_count;
	int best = -1;
	int best_sat = -1;
	int best_deg = -1;
	std::vector<char> used(static_cast<std::size_t>(std::max(1, current_max_colour + 1)), 0);

	for (int v = 0; v < n; ++v) {
		if (colours[v] != -1) continue;
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

struct ProgressState {
	std::chrono::steady_clock::time_point start_time{std::chrono::steady_clock::now()};
	std::chrono::steady_clock::time_point last_report{start_time};
	long long nodes_visited{0};
	double interval_sec{5.0};
};

void maybe_report(ProgressState &state,
				  int coloured_count,
				  int current_max_colour,
				  int best_k,
				  int n) {
	const auto now = std::chrono::steady_clock::now();
	const double since_last = std::chrono::duration<double>(now - state.last_report).count();
	if (since_last < state.interval_sec) return;
	const double elapsed = std::chrono::duration<double>(now - state.start_time).count();
	std::cerr << "[exact_solver progress] elapsed=" << elapsed << "s"
		<< " coloured=" << coloured_count << "/" << n
		<< " current_palette=" << (current_max_colour + 1)
		<< " best_k=" << best_k
		<< " nodes=" << state.nodes_visited
		<< '\n';
	state.last_report = now;
}

void backtrack_exact(const Graph &g,
					 std::vector<int> &colours,
					 int coloured_count,
					 int current_max_colour,
					 int &best_k,
					 std::vector<int> &best_solution,
					 ProgressState &progress) {
	const int n = g.vertex_count;
	progress.nodes_visited++;
	maybe_report(progress, coloured_count, current_max_colour, best_k, n);

	if (coloured_count == n) {
		const int used = current_max_colour + 1;
		if (used < best_k) {
			best_k = used;
			best_solution = colours;
		}
		return;
	}

	if (current_max_colour + 1 >= best_k) return;

	const int u = select_vertex(g, colours, current_max_colour);
	if (u == -1) return;

	std::vector<char> banned(static_cast<std::size_t>(std::max(1, current_max_colour + 1)), 0);
	for (int nb : g.adjacency_list[u]) {
		int c = colours[nb];
		if (c >= 0 && c <= current_max_colour) banned[c] = 1;
	}

	for (int c = 0; c <= current_max_colour; ++c) {
		if (banned[c]) continue;
		colours[u] = c;
		backtrack_exact(g, colours, coloured_count + 1, current_max_colour, best_k, best_solution, progress);
		colours[u] = -1;
	}

	if (current_max_colour + 2 < best_k) {
		colours[u] = current_max_colour + 1;
		backtrack_exact(g, colours, coloured_count + 1, current_max_colour + 1, best_k, best_solution, progress);
		colours[u] = -1;
	}
}

} // namespace

std::vector<int> colour_with_exact(const Graph &graph) {
	const int n = graph.vertex_count;
	if (n == 0) return {};

	std::vector<int> ub_solution = colour_with_dsatur(graph);
	int best_k = count_colours(ub_solution);
	if (best_k <= 1) return std::vector<int>(n, n ? 0 : -1);

	std::vector<int> colours(n, -1);
	std::vector<int> best_solution = ub_solution;

	ProgressState progress;
	if (const char *env = std::getenv("EXACT_PROGRESS_INTERVAL")) {
		try {
			double val = std::stod(env);
			if (val >= 0.05 && val <= 600.0) progress.interval_sec = val;
		} catch (...) {
			// ignore invalid
		}
	}

	backtrack_exact(graph, colours, 0, -1, best_k, best_solution, progress);

	// Force a final report
	progress.last_report = progress.start_time - std::chrono::seconds(10);
	maybe_report(progress, n, count_colours(best_solution) - 1, best_k, n);

	return best_solution;
}

std::vector<int> colour_with_exact_snapshots(const Graph &graph, const std::string &snapshots_path) {
	const int n = graph.vertex_count;
	if (n == 0) return {};

	std::ofstream out(snapshots_path);
	if (!out.is_open()) {
		throw std::runtime_error("Failed to open exact-solver snapshots file: " + snapshots_path);
	}

	auto write_snapshot = [&](const std::vector<int> &colours){
		for (int i = 0; i < (int)colours.size(); ++i) {
			if (i) out << ' ';
			out << colours[i];
		}
		out << '\n';
	};

	std::vector<int> ub_solution = colour_with_dsatur(graph);
	int best_k = count_colours(ub_solution);
	if (best_k <= 1) {
		write_snapshot(std::vector<int>(n, 0));
		return std::vector<int>(n, n ? 0 : -1);
	}

	std::vector<int> colours(n, -1);
	std::vector<int> best_solution = ub_solution;
	write_snapshot(best_solution);

	ProgressState progress;
	if (const char *env = std::getenv("EXACT_PROGRESS_INTERVAL")) {
		try {
			double val = std::stod(env);
			if (val >= 0.05 && val <= 600.0) progress.interval_sec = val;
		} catch (...) {}
	}

	// wrap backtrack to capture improvements
	std::function<void(const Graph&, std::vector<int>&, int, int, int&, std::vector<int>&, ProgressState&)> rec;
	rec = [&](const Graph &g, std::vector<int> &col, int coloured_count, int current_max_colour, int &bk, std::vector<int> &best_sol, ProgressState &prog){
		const int before_best = bk;
		backtrack_exact(g, col, coloured_count, current_max_colour, bk, best_sol, prog);
		if (bk < before_best) {
			write_snapshot(best_sol);
		}
	};

	rec(graph, colours, 0, -1, best_k, best_solution, progress);

	progress.last_report = progress.start_time - std::chrono::seconds(10);
	maybe_report(progress, n, count_colours(best_solution) - 1, best_k, n);
	write_snapshot(best_solution);
	return best_solution;
}

} // namespace graph_colouring
