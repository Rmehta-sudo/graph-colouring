#pragma once

#include <string>
#include <vector>
#include <optional>

namespace graph_colouring {

struct Graph {
	int vertex_count = 0;
	int edge_count = 0;
	std::vector<std::vector<int>> adjacency_list;
};

struct BenchmarkResult {
	std::string algorithm_name;
	std::string graph_name;
	int vertex_count = 0;
	int edge_count = 0;
	int color_count = 0;
	std::optional<int> known_optimal;
	double runtime_ms = 0.0;
};

// IO
Graph load_graph(const std::string &path);
void write_coloring(const std::string &path, const Graph &graph, const std::vector<int> &colours);
void append_result_csv(const std::string &path, const BenchmarkResult &result);

} // namespace graph_colouring
