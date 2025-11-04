#pragma once

#include <vector>

#include "../utils.h"

namespace graph_colouring {

std::vector<int> colour_with_genetic(const Graph &graph,
                                     int population_size = 64,
                                     int max_generations = 500,
                                     double mutation_rate = 0.02);

}  // namespace graph_colouring
