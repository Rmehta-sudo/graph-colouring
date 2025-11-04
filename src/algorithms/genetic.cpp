#include "genetic.h"

#include <algorithm>
#include <numeric>
#include <random>

namespace graph_colouring {

namespace {

struct Individual {
	std::vector<int> colours;
	int conflicts{};
	int colour_usage{};
};

int max_degree(const Graph &graph) {
	int result = 0;
	for (const auto &neighbours : graph.adjacency_list) {
		result = std::max<int>(result, neighbours.size());
	}
	return result;
}

int count_colour_usage(const std::vector<int> &colours) {
	int max_colour = -1;
	for (int colour : colours) {
		max_colour = std::max(max_colour, colour);
	}
	return max_colour >= 0 ? (max_colour + 1) : 0;
}

int count_conflicts(const Graph &graph, const std::vector<int> &colours) {
	int conflicts = 0;
	const int n = graph.vertex_count;
	for (int u = 0; u < n; ++u) {
		const int colour = colours[u];
		for (int v : graph.adjacency_list[u]) {
			if (u < v && colour == colours[v]) {
				++conflicts;
			}
		}
	}
	return conflicts;
}

void evaluate(Individual &individual, const Graph &graph) {
	individual.conflicts = count_conflicts(graph, individual.colours);
	individual.colour_usage = count_colour_usage(individual.colours);
}

bool better(const Individual &lhs, const Individual &rhs) {
	if (lhs.conflicts != rhs.conflicts) {
		return lhs.conflicts < rhs.conflicts;
	}
	if (lhs.colour_usage != rhs.colour_usage) {
		return lhs.colour_usage < rhs.colour_usage;
	}
	return lhs.colours < rhs.colours;
}

Individual crossover(const Individual &a,
					 const Individual &b,
					 std::mt19937 &rng,
					 int palette) {
	const int n = static_cast<int>(a.colours.size());
	Individual child;
	child.colours.resize(n);
	if (n == 0) {
		return child;
	}
	std::uniform_int_distribution<int> cut_dist(1, std::max(1, n - 1));
	const int cut = cut_dist(rng);
	for (int i = 0; i < n; ++i) {
		child.colours[i] = (i < cut) ? a.colours[i] : b.colours[i];
		child.colours[i] = std::clamp(child.colours[i], 0, palette - 1);
	}
	return child;
}

void mutate(Individual &individual,
			std::mt19937 &rng,
			int palette,
			double mutation_rate) {
	if (individual.colours.empty()) {
		return;
	}
	std::uniform_real_distribution<double> chance(0.0, 1.0);
	std::uniform_int_distribution<int> vertex_dist(0, static_cast<int>(individual.colours.size()) - 1);
	std::uniform_int_distribution<int> colour_dist(0, palette - 1);
	if (chance(rng) < mutation_rate) {
		const int index = vertex_dist(rng);
		individual.colours[index] = colour_dist(rng);
	}
}

const Individual &tournament_select(const std::vector<Individual> &population,
									std::mt19937 &rng) {
	std::uniform_int_distribution<std::size_t> pick(0, population.size() - 1);
	const Individual *best = nullptr;
	constexpr int tournament_size = 3;
	for (int i = 0; i < tournament_size; ++i) {
		const Individual &candidate = population[pick(rng)];
		if (best == nullptr || better(candidate, *best)) {
			best = &candidate;
		}
	}
	return *best;
}

std::vector<int> greedy_repair(const Graph &graph,
							   const std::vector<int> &seed,
							   int palette) {
	const int n = graph.vertex_count;
	std::vector<int> order(n);
	std::iota(order.begin(), order.end(), 0);
	std::sort(order.begin(), order.end(), [&](int lhs, int rhs) {
		return graph.adjacency_list[lhs].size() > graph.adjacency_list[rhs].size();
	});

	const int palette_limit = palette + n;
	std::vector<int> colours(n, -1);
	std::vector<char> banned(palette_limit, 0);

	for (int vertex : order) {
		std::fill(banned.begin(), banned.end(), 0);
		for (int neighbour : graph.adjacency_list[vertex]) {
			const int neighbour_colour = (neighbour < n) ? colours[neighbour] : -1;
			if (neighbour_colour >= 0 && neighbour_colour < palette_limit) {
				banned[neighbour_colour] = 1;
			}
		}

		int preferred = (vertex < static_cast<int>(seed.size())) ? seed[vertex] : -1;
		if (preferred >= 0 && preferred < palette_limit && !banned[preferred]) {
			colours[vertex] = preferred;
			continue;
		}

		int colour = 0;
		while (colour < palette_limit && banned[colour]) {
			++colour;
		}
		if (colour >= palette_limit) {
			colour = palette_limit - 1;
		}
		colours[vertex] = colour;
	}

	return colours;
}

}  // namespace

std::vector<int> colour_with_genetic(const Graph &graph,
									 int population_size,
									 int max_generations,
									 double mutation_rate) {
	const int n = graph.vertex_count;
	if (n == 0) {
		return {};
	}

	population_size = std::max(4, population_size + (population_size % 2));
	const int palette = std::max(1, max_degree(graph) + 1);

	std::mt19937 rng(std::random_device{}());
	std::uniform_int_distribution<int> colour_dist(0, palette - 1);

	std::vector<Individual> population(population_size);
	for (auto &individual : population) {
		individual.colours.resize(n);
		for (int v = 0; v < n; ++v) {
			individual.colours[v] = colour_dist(rng);
		}
		evaluate(individual, graph);
	}

	Individual best = population.front();
	for (const auto &individual : population) {
		if (better(individual, best)) {
			best = individual;
		}
	}

	std::vector<Individual> next_population;
	next_population.reserve(population_size);

	for (int generation = 0; generation < max_generations; ++generation) {
		std::sort(population.begin(), population.end(), better);
		if (better(population.front(), best)) {
			best = population.front();
		}
		if (best.conflicts == 0) {
			break;
		}

		next_population.clear();
		const int elites = std::min(2, population_size);
		for (int i = 0; i < elites; ++i) {
			next_population.push_back(population[i]);
		}

		while (static_cast<int>(next_population.size()) < population_size) {
			const Individual &parent_a = tournament_select(population, rng);
			const Individual &parent_b = tournament_select(population, rng);

			Individual child = crossover(parent_a, parent_b, rng, palette);
			mutate(child, rng, palette, mutation_rate);
			evaluate(child, graph);
			next_population.push_back(std::move(child));
		}

		population.swap(next_population);
	}

	if (best.conflicts != 0) {
		return greedy_repair(graph, best.colours, palette);
	}
	return best.colours;
}

}  // namespace graph_colouring
