#include "utils.h"

#include "algorithms/genetic.h"

#include <chrono>
#include <filesystem>
#include <functional>
#include <iostream>
#include <optional>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <vector>

namespace graph_colouring {

struct Options {
	std::string algorithm;
	std::string input_path;
	std::string output_path;
	std::string results_path;
	std::string graph_name;
	std::optional<int> known_optimal;
};

namespace {

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
		} else if (arg == "--help" || arg == "-h") {
			std::cout << "Usage: benchmark_runner --algorithm NAME --input FILE [options]\n"
					  << "  Options:\n"
					  << "    --output FILE           Write colouring to FILE\n"
					  << "    --results FILE          Append metrics to FILE\n"
					  << "    --graph-name NAME       Override graph identifier\n"
					  << "    --known-optimal VALUE   Known chromatic number\n";
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

std::function<std::vector<int>(const Graph &)> make_stub(const std::string &name) {
	return [name](const Graph &graph) -> std::vector<int> {
		(void)graph;
		throw std::logic_error("Algorithm not implemented: " + name);
	};
}

std::unordered_map<std::string, std::function<std::vector<int>(const Graph &)>>
build_algorithm_table() {
	return {
		{"welsh_powell", make_stub("welsh_powell")},
		{"dsatur", make_stub("dsatur")},
		{"simulated_annealing", make_stub("simulated_annealing")},
	{"genetic", [](const Graph &graph) { return colour_with_genetic(graph); }},
		{"exact_solver", make_stub("exact_solver")},
	};
}

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
		const std::vector<int> colours = finder->second(graph);
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
			result.known_optimal = options.known_optimal;
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
