/**
 * @file benchmark_runner.cpp
 * @brief Command-line interface for running graph colouring algorithms.
 *
 * This file provides a CLI tool for executing various graph colouring algorithms
 * on DIMACS-format graph files. Features include:
 * - Multiple algorithm support (welsh_powell, dsatur, genetic, simulated_annealing, exact_solver)
 * - Colouring output to file
 * - Benchmark results logging to CSV
 * - Optional snapshot generation for animation
 * - Automatic known-optimal lookup from metadata files
 *
 * Usage: benchmark_runner --algorithm NAME --input FILE [options]
 */

#include "utils.h"

#include "algorithms/genetic.h"
#include "algorithms/welsh_powell.h"
#include "algorithms/dsatur.h"
#include "algorithms/simulated_annealing.h"
#include "algorithms/exact_solver.h"

#include <chrono>
#include <filesystem>
#include <functional>
#include <fstream>
#include <sstream>
#include <iostream>
#include <optional>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

namespace graph_colouring {

/**
 * @brief Command-line options for the benchmark runner.
 */
struct Options {
	std::string algorithm;         ///< Name of the algorithm to run
	std::string input_path;        ///< Path to input graph file (DIMACS format)
	std::string output_path;       ///< Path to write colouring output
	std::string results_path;      ///< Path to append benchmark results CSV
	std::string graph_name;        ///< Identifier for the graph in results
	std::optional<int> known_optimal;  ///< Known chromatic number (if available)
    bool save_snapshots{false};    ///< Whether to save per-step snapshots
	// Genetic algorithm tuning (optional)
	int population_size{64};       ///< Population size for genetic algorithm
	int max_generations{500};      ///< Maximum generations for genetic algorithm
	double mutation_rate{0.02};    ///< Mutation rate for genetic algorithm
};

namespace {

/**
 * @brief Look up known optimal chromatic number from metadata CSV files.
 *
 * Searches metadata files for the given graph name and returns
 * the known optimal value if found.
 *
 * @param graph_name Name of the graph (with or without .col extension).
 * @return std::optional<int> Known chromatic number, or nullopt if not found.
 */
std::optional<int> lookup_known_optimal_from_metadata(const std::string &graph_name) {
	const std::vector<std::filesystem::path> candidates = {
		std::filesystem::path("scripts/datasets/metadata-dimacs.csv"),
		std::filesystem::path("scripts/datasets/metadata-generated.csv"),
	};
	const std::string with_ext = (graph_name.size() >= 4 && graph_name.substr(graph_name.size()-4)==".col")
		? graph_name
		: (graph_name + ".col");
	for (const auto &path : candidates) {
		if (!std::filesystem::exists(path)) continue;
		std::ifstream in(path);
		if (!in.is_open()) continue;
		std::string header;
		std::getline(in, header);
		std::string line;
		while (std::getline(in, line)) {
			if (line.empty()) continue;
			// naive CSV split (fields have no embedded commas in our metadata)
			std::vector<std::string> fields;
			std::stringstream ss(line);
			std::string cell;
			while (std::getline(ss, cell, ',')) fields.push_back(cell);
			if (fields.empty()) continue;
			// Expect: graph_name,source,vertices,edges,density,known_optimal,path,graph_type,notes
			if (fields.size() < 6) continue;
			const std::string &gname = fields[0];
			const std::string &known = fields[5];
			if (gname == graph_name || gname == with_ext) {
				if (!known.empty()) {
					try {
						return std::stoi(known);
					} catch (...) {
						return std::nullopt;
					}
				}
				return std::nullopt;
			}
		}
	}
	return std::nullopt;
}

/**
 * @brief Parse a string as an optional integer.
 * @param value String to parse.
 * @return std::optional<int> Parsed integer, or nullopt if empty.
 * @throws std::invalid_argument If string is non-empty but not a valid integer.
 */
std::optional<int> parse_optional_int(const std::string &value) {
	if (value.empty()) {
		return std::nullopt;
	}
	try {
		return std::stoi(value);
	} catch (const std::exception &) {
		throw std::invalid_argument("Failed to parse integer value: " + value);
	}
}

}  // namespace

/**
 * @brief Parse command-line arguments into Options struct.
 *
 * @param argc Argument count.
 * @param argv Argument values.
 * @return Options Parsed command-line options.
 * @throws std::invalid_argument If required arguments are missing or invalid.
 */
Options parse_arguments(int argc, char **argv) {
	Options options;
	for (int i = 1; i < argc; ++i) {
		std::string arg = argv[i];
		auto require_value = [&](const std::string &flag) -> std::string {
			if (i + 1 >= argc) {
				throw std::invalid_argument(flag + " requires a value");
			}
			return std::string(argv[++i]);
		};

		if (arg == "--algorithm" || arg == "-a") {
			options.algorithm = require_value(arg);
		} else if (arg == "--input" || arg == "-i") {
			options.input_path = require_value(arg);
		} else if (arg == "--output" || arg == "-o") {
			options.output_path = require_value(arg);
		} else if (arg == "--results" || arg == "-r") {
			options.results_path = require_value(arg);
		} else if (arg == "--graph-name" || arg == "-g") {
			options.graph_name = require_value(arg);
		} else if (arg == "--known-optimal") {
			options.known_optimal = parse_optional_int(require_value(arg));
		} else if (arg == "--save-snapshots") {
			options.save_snapshots = true;
		} else if (arg == "--population-size") {
			options.population_size = std::stoi(require_value(arg));
			if (options.population_size < 2) options.population_size = 2;
		} else if (arg == "--generations") {
			options.max_generations = std::stoi(require_value(arg));
			if (options.max_generations < 1) options.max_generations = 1;
		} else if (arg == "--mutation-rate") {
			options.mutation_rate = std::stod(require_value(arg));
			if (options.mutation_rate < 0.0) options.mutation_rate = 0.0;
			if (options.mutation_rate > 1.0) options.mutation_rate = 1.0;
		} else if (arg == "--help" || arg == "-h") {
			std::cout << "Usage: benchmark_runner --algorithm NAME --input FILE [options]\n"
					  << "  Options:\n"
					  << "    --output FILE           Write colouring to FILE\n"
					  << "    --results FILE          Append metrics to FILE\n"
					  << "    --graph-name NAME       Override graph identifier\n"
					  << "    --known-optimal VALUE   Known chromatic number\n"
					  << "    --save-snapshots        Write per-iteration/epoch snapshots (supported by dsatur, welsh_powell, genetic, simulated_annealing, exact_solver)\n"
					  << "\n  Genetic algorithm tuning (when -a genetic):\n"
					  << "    --population-size N     Population size (default 64)\n"
					  << "    --generations N         Max generations (default 500)\n"
					  << "    --mutation-rate X       Mutation rate in [0,1] (default 0.02)\n";
			std::exit(0);
		} else {
			throw std::invalid_argument("Unknown argument: " + arg);
		}
	}

	if (options.algorithm.empty()) {
		throw std::invalid_argument("--algorithm is required");
	}
	if (options.input_path.empty()) {
		throw std::invalid_argument("--input is required");
	}
	if (options.graph_name.empty()) {
		options.graph_name = std::filesystem::path(options.input_path).filename().string();
	}
	return options;
}

namespace {

/**
 * @brief Build a mapping from algorithm names to their execution functions.
 * @return std::unordered_map Mapping of algorithm name to colouring function.
 */
std::unordered_map<std::string, std::function<std::vector<int>(const Graph &)>>
build_algorithm_table() {
	return {
		{"welsh_powell", [](const Graph &graph) { return colour_with_welsh_powell(graph); }},
		{"dsatur", [](const Graph &graph) { return colour_with_dsatur(graph); }},
		{"simulated_annealing", [](const Graph &graph) { return colour_with_simulated_annealing(graph); }},
		{"genetic", [](const Graph &graph) { return colour_with_genetic(graph); }},
		{"exact_solver", [](const Graph &graph) { return colour_with_exact(graph); }},
	};
}

/**
 * @brief Count the number of distinct colours used in a colouring.
 * @param colours Colour assignment vector.
 * @return int Number of colours used (max_colour + 1).
 */
int count_colours(const std::vector<int> &colours) {
	int max_colour = -1;
	for (int colour : colours) {
		if (colour > max_colour) {
			max_colour = colour;
		}
	}
	return max_colour >= 0 ? (max_colour + 1) : 0;
}

}  // namespace

}  // namespace graph_colouring

/**
 * @brief Main entry point for the benchmark runner.
 *
 * Parses command-line arguments, loads the input graph, runs the specified
 * algorithm, and outputs results to the specified destinations.
 *
 * @param argc Argument count.
 * @param argv Argument values.
 * @return int Exit code (0 on success, 1 on error).
 */
int main(int argc, char **argv) {
	using namespace graph_colouring;

	try {
		const Options options = parse_arguments(argc, argv);
		const Graph graph = load_graph(options.input_path);

		auto strategies = build_algorithm_table();
		const auto finder = strategies.find(options.algorithm);
		if (finder == strategies.end()) {
			throw std::invalid_argument("Unknown algorithm: " + options.algorithm);
		}

		const auto start = std::chrono::high_resolution_clock::now();

		// Prepare snapshots path if requested and applicable
		std::vector<int> colours;
		if (options.save_snapshots) {
			std::filesystem::create_directories("output/snapshots");
			const std::string snap_file = std::string("output/snapshots/") + options.algorithm + "-" + options.graph_name + "-snapshots.txt";
			if (options.algorithm == "dsatur") {
				colours = colour_with_dsatur_snapshots(graph, snap_file);
			} else if (options.algorithm == "welsh_powell") {
				colours = colour_with_welsh_powell_snapshots(graph, snap_file);
			} else if (options.algorithm == "genetic") {
				colours = colour_with_genetic_snapshots(graph, snap_file, options.population_size, options.max_generations, options.mutation_rate);
			} else if (options.algorithm == "simulated_annealing") {
				colours = colour_with_simulated_annealing_snapshots(graph, snap_file);
			} else if (options.algorithm == "exact_solver") {
				colours = colour_with_exact_snapshots(graph, snap_file);
			} else {
				colours = finder->second(graph);
			}
		} else {
			if (options.algorithm == "genetic") {
				colours = colour_with_genetic(graph, options.population_size, options.max_generations, options.mutation_rate);
			} else {
				colours = finder->second(graph);
			}
		}
		const auto stop = std::chrono::high_resolution_clock::now();
		const double runtime_ms = std::chrono::duration<double, std::milli>(stop - start).count();

		if (static_cast<int>(colours.size()) != graph.vertex_count) {
			throw std::runtime_error("Algorithm returned colour vector of incorrect size");
		}

		if (!options.output_path.empty()) {
			write_coloring(options.output_path, graph, colours);
		}

		if (!options.results_path.empty()) {
			BenchmarkResult result;
			result.algorithm_name = options.algorithm;
			result.graph_name = options.graph_name;
			result.vertex_count = graph.vertex_count;
			result.edge_count = graph.edge_count;
			result.color_count = count_colours(colours);
			// Prefer CLI-provided known optimal, else try metadata lookup
			if (options.known_optimal.has_value()) {
				result.known_optimal = options.known_optimal;
			} else {
				result.known_optimal = lookup_known_optimal_from_metadata(result.graph_name);
			}
			result.runtime_ms = runtime_ms;
			append_result_csv(options.results_path, result);
		}

		std::cout << "Algorithm " << options.algorithm << " completed in " << runtime_ms << " ms" << std::endl;
		return 0;
	} catch (const std::exception &error) {
		std::cerr << "Error: " << error.what() << std::endl;
		return 1;
	}
}
