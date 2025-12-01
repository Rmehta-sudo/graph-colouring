/**
 * @file utils.h
 * @brief Core data structures and utility function declarations for graph colouring.
 * 
 * This header defines the fundamental types used throughout the graph colouring
 * benchmark suite, including the Graph representation and benchmark result storage.
 */

#pragma once

#include <optional>
#include <string>
#include <vector>

namespace graph_colouring {

/**
 * @struct Graph
 * @brief Represents an undirected graph using adjacency list representation.
 * 
 * The graph uses 0-based vertex indexing internally, though DIMACS files use 1-based.
 */
struct Graph {
	int vertex_count{};                              ///< Number of vertices (|V|)
	int edge_count{};                                ///< Number of edges (|E|)
	std::vector<std::vector<int>> adjacency_list;    ///< Adjacency list: adjacency_list[u] contains neighbours of vertex u
};

/**
 * @struct BenchmarkResult
 * @brief Stores the results of a single algorithm run for CSV logging.
 */
struct BenchmarkResult {
	std::string algorithm_name;          ///< Name of the algorithm used
	std::string graph_name;              ///< Identifier for the input graph
	int vertex_count{};                  ///< Number of vertices in the graph
	int edge_count{};                    ///< Number of edges in the graph
	int color_count{};                   ///< Number of colours used in the solution
	std::optional<int> known_optimal;    ///< Known chromatic number (if available)
	double runtime_ms{};                 ///< Execution time in milliseconds
};

/**
 * @brief Loads a graph from a DIMACS-format .col file.
 * 
 * Parses the standard DIMACS edge format with 'p edge V E' header and 'e u v' edge lines.
 * Handles comments (lines starting with 'c', '%', '#'), removes self-loops and duplicates.
 * 
 * @param path Filesystem path to the .col file.
 * @return Graph The loaded graph with adjacency list representation.
 * @throws std::runtime_error If file cannot be opened or format is invalid.
 */
Graph load_graph(const std::string &path);

/**
 * @brief Writes a graph colouring solution to a file in DIMACS format.
 * 
 * Output format: 'v <vertex> <colour>' lines (1-indexed vertices).
 * 
 * @param path Filesystem path for the output file.
 * @param graph The original graph (for metadata).
 * @param colors Vector of colour assignments (0-indexed colours).
 * @throws std::runtime_error If file cannot be opened.
 * @throws std::invalid_argument If colours vector size doesn't match vertex count.
 */
void write_coloring(const std::string &path, const Graph &graph, const std::vector<int> &colors);

/**
 * @brief Appends benchmark results to a CSV file.
 * 
 * Creates the file with headers if it doesn't exist. Thread-safe for sequential calls.
 * 
 * @param path Filesystem path to the CSV file.
 * @param result The benchmark result to append.
 * @throws std::runtime_error If file cannot be opened for writing.
 */
void append_result_csv(const std::string &path, const BenchmarkResult &result);

}  // namespace graph_colouring
