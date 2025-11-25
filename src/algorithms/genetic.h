#pragma once

#include <vector>
#include <string>
#include "../utils.h"

namespace graph_colouring {

// Optimized Genetic Algorithm for Graph Colouring
// Includes GPX-lite crossover, conflict-focused mutation, adaptive mutation rate,
// warm-start seeding between palette runs, and greedy elite refinement.

std::vector<int> colour_with_genetic(const Graph &graph,
                                     int population_size = 64,
                                     int max_generations = 300,
                                     double initial_mutation_rate = 0.03);

// Genetic algorithm with snapshots: writes the best individual's colour vector
// (space-separated; -1 if any placeholder though GA keeps non-negative) after
// initial population evaluation and after each generation where an improvement
// in fitness is observed. The final line is the best solution achieved.
// Returns that best colour vector.
std::vector<int> colour_with_genetic_snapshots(const Graph &graph,
                                               const std::string &snapshots_path,
                                               int population_size = 64,
                                               int max_generations = 300,
                                               double initial_mutation_rate = 0.03);

}  // namespace graph_colouring
