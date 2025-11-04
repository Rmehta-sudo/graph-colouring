#include "../utils.h"

#include <algorithm>
#include <fstream>
#include <sstream>
#include <stdexcept>

namespace graph_colouring {

Graph load_graph(const std::string &path) {
	std::ifstream input(path);
	if (!input.is_open()) {
		throw std::runtime_error("Failed to open graph file: " + path);
	}

	Graph graph;
	int edges_added = 0;
	std::string line;
	while (std::getline(input, line)) {
		if (line.empty()) {
			continue;
		}
		const char lead = line[0];
		if (lead == 'c' || lead == '%' || lead == '#') {
			continue;
		}
		if (lead == 'p') {
			std::istringstream header(line);
			std::string tag;
			header >> tag;  // p
			header >> tag;  // edge or edges
			header >> graph.vertex_count;
			header >> graph.edge_count;
			if (graph.vertex_count <= 0) {
				throw std::runtime_error("Invalid vertex count in " + path);
			}
			graph.adjacency_list.assign(graph.vertex_count, {});
		} else if (lead == 'e') {
			if (graph.adjacency_list.empty()) {
				throw std::runtime_error("Encountered edge before problem line in " + path);
			}
			std::istringstream edge_stream(line);
			char tag;
			int u;
			int v;
			edge_stream >> tag >> u >> v;
			if (u <= 0 || v <= 0 || u > graph.vertex_count || v > graph.vertex_count) {
				throw std::runtime_error("Edge references out-of-range vertex in " + path);
			}
			if (u == v) {
				continue;
			}
			--u;
			--v;
			auto &adj_u = graph.adjacency_list[u];
			auto &adj_v = graph.adjacency_list[v];
			if (std::find(adj_u.begin(), adj_u.end(), v) != adj_u.end()) {
				continue;
			}
			adj_u.push_back(v);
			adj_v.push_back(u);
			++edges_added;
		}
	}

	if (graph.vertex_count == 0) {
		throw std::runtime_error("Graph file missing problem line: " + path);
	}
	graph.edge_count = edges_added;
	return graph;
}

}  // namespace graph_colouring
