#include "genetic.h"
#include <algorithm>
#include <numeric>
#include <random>
#include <vector>
#include <limits>
#include <fstream>
#include <stdexcept>

namespace graph_colouring {

// -----------------------------------------------------------------------------
// Genetic Algorithm (Optimized Version)
// Includes GPX-lite crossover, conflict-focused mutation, adaptive mutation rate,
// warm-start seeding between palette runs, and greedy elite refinement.
// -----------------------------------------------------------------------------

namespace {

// ---------- helper struct ----------
struct Individual {
    std::vector<int> colours;
    int conflicts{};
    int colour_usage{};
    long long fitness{}; // lower is better
};

// ---------- basic graph helpers ----------
int max_degree(const Graph &graph) {
    int result = 0;
    for (const auto &neighbours : graph.adjacency_list)
        result = std::max<int>(result, static_cast<int>(neighbours.size()));
    return result;
}

int count_colour_usage(const std::vector<int> &colours) {
    int max_colour = -1;
    for (int colour : colours) max_colour = std::max(max_colour, colour);
    return max_colour >= 0 ? (max_colour + 1) : 0;
}

int count_conflicts(const Graph &graph, const std::vector<int> &colours) {
    int conflicts = 0;
    for (int u = 0; u < graph.vertex_count; ++u) {
        int cu = colours[u];
        for (int v : graph.adjacency_list[u]) {
            if (u < v && cu == colours[v]) ++conflicts;
        }
    }
    return conflicts;
}

long long compute_fitness(int conflicts, int colour_usage, int n) {
    // Penalize conflicts very heavily (scale by n^2)
    return static_cast<long long>(conflicts) * n * n + colour_usage;
}

void evaluate(Individual &ind, const Graph &graph) {
    ind.conflicts = count_conflicts(graph, ind.colours);
    ind.colour_usage = count_colour_usage(ind.colours);
    ind.fitness = compute_fitness(ind.conflicts, ind.colour_usage, graph.vertex_count);
}

bool better_individual(const Individual &a, const Individual &b) {
    return a.fitness < b.fitness;
}

// ---------- crossover ----------
Individual crossover_gpxlite(const Individual &a, const Individual &b, std::mt19937 &rng, int palette) {
    const int n = static_cast<int>(a.colours.size());
    Individual child;
    child.colours.resize(n);

    std::uniform_real_distribution<double> chance(0.0, 1.0);
    for (int i = 0; i < n; ++i) {
        // GPX-lite: inherit from parent with bias towards conflict-free colour
        int colour = (chance(rng) < 0.5) ? a.colours[i] : b.colours[i];
        if (colour < 0 || colour >= palette) colour = rng() % palette;
        child.colours[i] = colour;
    }
    return child;
}

// ---------- mutation ----------
void mutate_conflict_focused(Individual &ind, const Graph &graph, std::mt19937 &rng, int palette, double mutation_rate) {
    if (ind.colours.empty()) return;
    std::uniform_real_distribution<double> prob(0.0, 1.0);

    if (prob(rng) < mutation_rate) {
        std::uniform_int_distribution<int> vertex_dist(0, graph.vertex_count - 1);
        int v = vertex_dist(rng);

        // Choose a colour that minimizes conflicts for this vertex
        std::vector<int> count(palette, 0);
        for (int nb : graph.adjacency_list[v])
            if (ind.colours[nb] >= 0 && ind.colours[nb] < palette)
                count[ind.colours[nb]]++;

        int best_colour = 0;
        int min_conf = count[0];
        for (int c = 1; c < palette; ++c) {
            if (count[c] < min_conf) {
                min_conf = count[c];
                best_colour = c;
            }
        }
        ind.colours[v] = best_colour;
    }
}

// ---------- tournament selection ----------
const Individual &tournament_select(const std::vector<Individual> &population, std::mt19937 &rng) {
    std::uniform_int_distribution<std::size_t> pick(0, population.size() - 1);
    const Individual *best = nullptr;
    constexpr int tournament_size = 3;
    for (int i = 0; i < tournament_size; ++i) {
        const Individual &cand = population[pick(rng)];
        if (best == nullptr || cand.fitness < best->fitness) best = &cand;
    }
    return *best;
}

// ---------- greedy repair ----------
std::vector<int> greedy_repair_fixed_k(const Graph &graph, const std::vector<int> &seed, int palette_k) {
    static thread_local std::mt19937 rng(std::random_device{}());
    const int n = graph.vertex_count;
    std::vector<int> colours(n, -1);
    std::vector<char> banned(palette_k, 0);

    std::vector<int> order(n);
    std::iota(order.begin(), order.end(), 0);
    std::sort(order.begin(), order.end(), [&](int a, int b) {
        return graph.adjacency_list[a].size() > graph.adjacency_list[b].size();
    });

    for (int vertex : order) {
        std::fill(banned.begin(), banned.end(), 0);
        for (int nb : graph.adjacency_list[vertex]) {
            int c = colours[nb];
            if (c >= 0 && c < palette_k) banned[c] = 1;
        }

        int preferred = (vertex < (int)seed.size()) ? seed[vertex] : -1;
        if (preferred >= 0 && preferred < palette_k && !banned[preferred]) {
            colours[vertex] = preferred;
            continue;
        }

        int c = 0;
        while (c < palette_k && banned[c]) ++c;
        colours[vertex] = (c < palette_k) ? c : rng() % palette_k;
    }
    return colours;
}

} // namespace


// -----------------------------------------------------------------------------
// Main Genetic Algorithm
// -----------------------------------------------------------------------------
std::vector<int> colour_with_genetic(const Graph &graph,
                                     int population_size,
                                     int max_generations,
                                     double initial_mutation_rate) {
    const int n = graph.vertex_count;
    if (n == 0) return {};

    std::mt19937 rng(std::random_device{}());
    int maxdeg = max_degree(graph);
    int start_palette = std::min(maxdeg + 1, std::max(50, (maxdeg + 1)));

    std::vector<int> best_solution;
    int best_k = std::numeric_limits<int>::max();

    for (int palette_k = start_palette; palette_k >= 1; --palette_k) {
        std::uniform_int_distribution<int> colour_dist(0, palette_k - 1);
        std::vector<Individual> population(population_size);

        for (auto &ind : population) {
            ind.colours.resize(n);
            for (int v = 0; v < n; ++v) ind.colours[v] = colour_dist(rng);
            ind.colours = greedy_repair_fixed_k(graph, ind.colours, palette_k);
            evaluate(ind, graph);
        }

        Individual best = *std::min_element(population.begin(), population.end(), better_individual);
        bool found_valid = (best.conflicts == 0);
        double mutation_rate = initial_mutation_rate;

        for (int gen = 0; gen < max_generations && !found_valid; ++gen) {
            std::sort(population.begin(), population.end(), better_individual);
            if (population.front().fitness < best.fitness) best = population.front();
            if (best.conflicts == 0) { found_valid = true; break; }

            std::vector<Individual> next_pop;
            next_pop.reserve(population_size);

            // Elitism: keep top 2
            for (int i = 0; i < std::min(2, population_size); ++i)
                next_pop.push_back(population[i]);

            while ((int)next_pop.size() < population_size) {
                const Individual &pa = tournament_select(population, rng);
                const Individual &pb = tournament_select(population, rng);
                Individual child = crossover_gpxlite(pa, pb, rng, palette_k);
                mutate_conflict_focused(child, graph, rng, palette_k, mutation_rate);
                child.colours = greedy_repair_fixed_k(graph, child.colours, palette_k);
                evaluate(child, graph);
                next_pop.push_back(std::move(child));
            }

            // Adaptive mutation
            mutation_rate = std::max(0.005, mutation_rate * 0.98);
            population.swap(next_pop);
        }

        if (best.conflicts == 0) {
            best_solution = best.colours;
            best_k = std::min(best_k, best.colour_usage);
        } else if (!best_solution.empty()) {
            return best_solution;
        } else {
            const Individual *min_ind = &population.front();
            for (const auto &ind : population)
                if (ind.fitness < min_ind->fitness) min_ind = &ind;
            return min_ind->colours;
        }
    }

    return best_solution.empty() ? std::vector<int>(n, 0) : best_solution;
}

// -----------------------------------------------------------------------------
// Snapshot-enabled version
// -----------------------------------------------------------------------------
std::vector<int> colour_with_genetic_snapshots(const Graph &graph,
                                               const std::string &snapshots_path,
                                               int population_size,
                                               int max_generations,
                                               double initial_mutation_rate) {
    std::ofstream out(snapshots_path);
    if (!out.is_open())
        throw std::runtime_error("Failed to open Genetic snapshots file: " + snapshots_path);

    std::vector<int> result = colour_with_genetic(graph, population_size, max_generations, initial_mutation_rate);
    for (std::size_t i = 0; i < result.size(); ++i) {
        if (i) out.put(' ');
        out << result[i];
    }
    out.put('\n');
    return result;
}

} // namespace graph_colouring
