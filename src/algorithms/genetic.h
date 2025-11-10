#pragma once

#include <vector>

#include "../utils.h"

namespace graph_colouring {

std::vector<int> colour_with_genetic(const Graph &graph,
                                     int population_size = 64,
                                     int max_generations = 500,
                                     double mutation_rate = 0.02);

// Genetic algorithm with snapshots: writes the best individual's colour vector
// (space-separated; -1 if any placeholder though GA keeps non-negative) after
// initial population evaluation and after each generation where an improvement
// in fitness is observed. The final line is the best solution achieved.
// Returns that best colour vector.
std::vector<int> colour_with_genetic_snapshots(const Graph &graph,
                                               const std::string &snapshots_path,
                                               int population_size = 64,
                                               int max_generations = 500,
                                               double mutation_rate = 0.02);

}  // namespace graph_colouring
