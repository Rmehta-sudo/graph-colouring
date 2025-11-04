#include "../utils.h"

#include <filesystem>
#include <fstream>
#include <iomanip>
#include <stdexcept>

namespace graph_colouring {

namespace {

std::string format_optional(const std::optional<int> &value) {
	if (!value.has_value()) {
		return "";
	}
	return std::to_string(value.value());
}

}  // namespace

void append_result_csv(const std::string &path, const BenchmarkResult &result) {
	const std::filesystem::path csv_path(path);
	const bool write_header = !std::filesystem::exists(csv_path) || std::filesystem::file_size(csv_path) == 0;

	std::ofstream stream(csv_path, std::ios::app);
	if (!stream.is_open()) {
		throw std::runtime_error("Failed to open results file: " + path);
	}

	if (write_header) {
		stream << "algorithm,graph_name,vertices,edges,colors_used,known_optimal,runtime_ms" << '\n';
	}

	stream << result.algorithm_name << ','
		   << result.graph_name << ','
		   << result.vertex_count << ','
		   << result.edge_count << ','
		   << result.color_count << ','
		   << format_optional(result.known_optimal) << ','
		   << std::fixed << std::setprecision(3) << result.runtime_ms << '\n';
}

}  // namespace graph_colouring
