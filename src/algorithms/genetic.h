/**
 * @file genetic.h
 * @brief Genetic Algorithm (GA) for graph colouring optimization.
 * 
 * Implements an evolutionary approach to graph colouring with:
 * - GPX-lite crossover for combining parent solutions
 * - Conflict-focused mutation for local improvement
 * - Adaptive mutation rate that decreases over generations
 * - Greedy elite refinement for solution repair
 * - Iterative palette reduction to minimize colour count
 * 
 * Time Complexity: O(P × G × V) where P=population size, G=generations, V=vertices.
 * Space Complexity: O(P × V) for population storage.
 */

#pragma once

#include <vector>
#include <string>
#include "../utils.h"

namespace graph_colouring {

/**
 * @brief Colours a graph using a Genetic Algorithm.
 * 
 * Algorithm:
 * 1. For each palette size k (decreasing from upper bound):
 *    a. Initialize random population with greedy repair
 *    b. Evolve population: selection, crossover, mutation
 *    c. If valid k-colouring found, record and try smaller k
 * 2. Return best valid colouring found
 * 
 * @param graph The input graph to colour.
 * @param population_size Number of individuals in the population (default: 64).
 * @param max_generations Maximum generations per palette size (default: 300).
 * @param initial_mutation_rate Starting mutation probability (default: 0.03).
 * @return std::vector<int> Colour assignments where result[v] is the colour of vertex v (0-indexed).
 */
std::vector<int> colour_with_genetic(const Graph &graph,
                                     int population_size = 64,
                                     int max_generations = 300,
                                     double initial_mutation_rate = 0.03);

/**
 * @brief Genetic Algorithm with snapshots for visualization.
 * 
 * Writes the best individual's colour vector after finding improved solutions.
 * Final line contains the best solution achieved.
 * 
 * @param graph The input graph to colour.
 * @param snapshots_path Filesystem path for the snapshot output file.
 * @param population_size Number of individuals in the population.
 * @param max_generations Maximum generations per palette size.
 * @param initial_mutation_rate Starting mutation probability.
 * @return std::vector<int> Colour assignments (same as colour_with_genetic).
 * @throws std::runtime_error If snapshot file cannot be opened.
 */
std::vector<int> colour_with_genetic_snapshots(const Graph &graph,
                                               const std::string &snapshots_path,
                                               int population_size = 64,
                                               int max_generations = 300,
                                               double initial_mutation_rate = 0.03);

}  // namespace graph_colouring
