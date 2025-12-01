#pragma once

#include <optional>
#include <string>
#include <vector>

namespace graph_colouring {

struct Graph {
	int vertex_count{};
	int edge_count{};
	std::vector<std::vector<int>> adjacency_list;
};

struct BenchmarkResult {
	std::string algorithm_name;
	std::string graph_name;
	int vertex_count{};
	int edge_count{};
	int color_count{};
	std::optional<int> known_optimal;
	double runtime_ms{};
};

Graph load_graph(const std::string &path);
void write_coloring(const std::string &path, const Graph &graph, const std::vector<int> &colors);
void append_result_csv(const std::string &path, const BenchmarkResult &result);

}  // namespace graph_colouring
