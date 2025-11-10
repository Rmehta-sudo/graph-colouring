#include "genetic.h"
#include <algorithm>
#include <numeric>
#include <random>
#include <vector>
#include <limits>
#include <fstream>
#include <stdexcept>

namespace graph_colouring {

namespace {

// ---------- helper types ----------
struct Individual {
    std::vector<int> colours;
    int conflicts{};
    int colour_usage{};
    long long fitness{}; // lower is better
};

// ---------- basic graph helpers ----------
int max_degree(const Graph &graph) {
    int result = 0;
    for (const auto &neighbours : graph.adjacency_list) {
        result = std::max<int>(result, static_cast<int>(neighbours.size()));
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
        const int cu = colours[u];
        for (int v : graph.adjacency_list[u]) {
            if (u < v && cu == colours[v]) {
                ++conflicts;
            }
        }
    }
    return conflicts;
}

// ---------- fitness: always prefers fewer colours, but penalises conflicts heavily ----------
long long compute_fitness(int conflicts, int colour_usage, int n) {
    // conflicts are extremely bad: multiply by n (or bigger) so even 1 conflict is worse than many colours
    // but colour_usage also matters, so keep it as additive term.
    return static_cast<long long>(conflicts) * (n) + static_cast<long long>(colour_usage);
}

// ---------- evaluate individual ----------
void evaluate(Individual &ind, const Graph &graph) {
    ind.conflicts = count_conflicts(graph, ind.colours);
    ind.colour_usage = count_colour_usage(ind.colours);
    ind.fitness = compute_fitness(ind.conflicts, ind.colour_usage, graph.vertex_count);
}

bool better_individual(const Individual &a, const Individual &b) {
    return a.fitness < b.fitness;
}

// ---------- crossover / mutation ----------
Individual crossover(const Individual &a, const Individual &b, std::mt19937 &rng, int palette) {
    const int n = static_cast<int>(a.colours.size());
    Individual child;
    child.colours.resize(n);
    if (n == 0) return child;

    std::uniform_int_distribution<int> cut_dist(1, std::max(1, n - 1));
    const int cut = cut_dist(rng);
    for (int i = 0; i < n; ++i) {
        child.colours[i] = (i < cut) ? a.colours[i] : b.colours[i];
        // clamp into allowed range
        if (child.colours[i] < 0) child.colours[i] = 0;
        if (child.colours[i] >= palette) child.colours[i] = palette - 1;
    }
    return child;
}

void mutate(Individual &ind, std::mt19937 &rng, int palette, double mutation_rate) {
    if (ind.colours.empty()) return;
    std::uniform_real_distribution<double> chance(0.0, 1.0);
    if (chance(rng) >= mutation_rate) return;
    std::uniform_int_distribution<int> vertex_dist(0, static_cast<int>(ind.colours.size()) - 1);
    std::uniform_int_distribution<int> colour_dist(0, palette - 1);
    const int idx = vertex_dist(rng);
    ind.colours[idx] = colour_dist(rng);
}

// ---------- tournament selection ----------
const Individual& tournament_select(const std::vector<Individual> &population, std::mt19937 &rng) {
    std::uniform_int_distribution<std::size_t> pick(0, population.size() - 1);
    const Individual *best = nullptr;
    constexpr int tournament_size = 3;
    for (int i = 0; i < tournament_size; ++i) {
        const Individual &cand = population[pick(rng)];
        if (best == nullptr || cand.fitness < best->fitness) best = &cand;
    }
    return *best;
}

// ---------- greedy repair (fast constructive) ----------
std::vector<int> greedy_repair_fixed_k(const Graph &graph, const std::vector<int> &seed, int palette_k) {
    // A fast constructive greedy that respects the given palette_k.
    // It tries to keep the seed colours if possible, otherwise assigns the first available colour in [0..palette_k-1].
    const int n = graph.vertex_count;
    std::vector<int> order(n);
    std::iota(order.begin(), order.end(), 0);

    // order by descending degree (simple heuristic)
    std::sort(order.begin(), order.end(), [&](int lhs, int rhs) {
        return graph.adjacency_list[lhs].size() > graph.adjacency_list[rhs].size();
    });

    std::vector<int> colours(n, -1);
    std::vector<char> banned(palette_k, 0);

    for (int vertex : order) {
        std::fill(banned.begin(), banned.end(), 0);
        for (int nb : graph.adjacency_list[vertex]) {
            int c = (nb < n) ? colours[nb] : -1;
            if (c >= 0 && c < palette_k) banned[c] = 1;
        }

        int preferred = (vertex < static_cast<int>(seed.size())) ? seed[vertex] : -1;
        if (preferred >= 0 && preferred < palette_k && !banned[preferred]) {
            colours[vertex] = preferred;
            continue;
        }

        int c = 0;
        while (c < palette_k && banned[c]) ++c;
        if (c >= palette_k) {
            // No free colour in palette_k -> choose a conflict-minimising colour (choose first)
            // we pick a colour with minimum conflicts among neighbours
            int best_c = 0;
            int best_conflicts = std::numeric_limits<int>::max();
            for (int tryc = 0; tryc < palette_k; ++tryc) {
                int conf = 0;
                for (int nb : graph.adjacency_list[vertex]) {
                    if (nb < n && colours[nb] == tryc) ++conf;
                }
                if (conf < best_conflicts) {
                    best_conflicts = conf;
                    best_c = tryc;
                }
            }
            colours[vertex] = best_c;
        } else {
            colours[vertex] = c;
        }
    }
    return colours;
}

} // namespace

// ---------- Public function: improved GA with adaptive palette shrinking ----------
std::vector<int> colour_with_genetic(const Graph &graph,
                                     int population_size,
                                     int max_generations,
                                     double mutation_rate) {
    const int n = graph.vertex_count;
    if (n == 0) return {};

    // sensible parameter sanitation
    population_size = std::max(6, population_size | 1); // ensure odd/even as convenient
    std::mt19937 rng(std::random_device{}());

    // Start palette: choose a moderate upper bound, not necessarily max_degree+1.
    // Using max_degree+1 is safe but often very large; we cap initial palette to speed up reduction.
    int maxdeg = max_degree(graph);
    int start_palette = std::min(maxdeg + 1, std::max(50, (maxdeg + 1))); // start at maxdeg+1 but ensure at least 50
    // For very large graphs, you might want to cap start_palette to e.g. 200 to push compression:
    const int HARD_CAP = std::max(200, start_palette);
    if (start_palette > HARD_CAP) start_palette = HARD_CAP;

    // We'll maintain the best found solution overall
    std::vector<int> best_solution;
    int best_k = std::numeric_limits<int>::max();

    // Adaptive loop: try decreasing k from start_palette down to 1 (or until fails consecutively).
    // To avoid repeated expensive runs for tiny steps, we can try step sizes; here keep it simple: decrement by 1.
    for (int palette_k = start_palette; palette_k >= 1; --palette_k) {
        // Initialize population for this k
        std::uniform_int_distribution<int> colour_dist(0, palette_k - 1);

        std::vector<Individual> population(population_size);
        for (auto &ind : population) {
            ind.colours.resize(n);
            // random init but biased: try to keep colours in a smaller range initially
            for (int v = 0; v < n; ++v) {
                ind.colours[v] = colour_dist(rng);
            }
            // quick local repair to make individuals stronger (optional but often useful)
            ind.colours = greedy_repair_fixed_k(graph, ind.colours, palette_k);
            evaluate(ind, graph);
        }

        // track best in this palette
        Individual best = population.front();
        for (const auto &ind : population) if (ind.fitness < best.fitness) best = ind;

        // generational loop
        std::vector<Individual> next_pop;
        next_pop.reserve(population_size);

        bool found_valid = (best.conflicts == 0);

        for (int gen = 0; gen < max_generations && !found_valid; ++gen) {
            std::sort(population.begin(), population.end(), [](const Individual &a, const Individual &b) {
                return a.fitness < b.fitness;
            });
            if (population.front().fitness < best.fitness) best = population.front();
            if (best.conflicts == 0) {
                found_valid = true;
                break;
            }

            next_pop.clear();
            // elitism: keep top 2
            int elites = std::min(2, population_size);
            for (int i = 0; i < elites; ++i) next_pop.push_back(population[i]);

            // fill rest
            while (static_cast<int>(next_pop.size()) < population_size) {
                const Individual &pa = tournament_select(population, rng);
                const Individual &pb = tournament_select(population, rng);
                Individual child = crossover(pa, pb, rng, palette_k);

                // mutate
                mutate(child, rng, palette_k, mutation_rate);

                // local greedy repair to reduce conflicts and colours under current palette
                child.colours = greedy_repair_fixed_k(graph, child.colours, palette_k);

                evaluate(child, graph);
                next_pop.push_back(std::move(child));
            }

            population.swap(next_pop);
        } // end generations

        // after generations check best
        // pick best from population again (safety)
        for (const auto &ind : population) if (ind.fitness < best.fitness) best = ind;

        if (best.conflicts == 0) {
            // we found a valid k-colouring
            best_solution = best.colours;
            best_k = std::min(best_k, best.colour_usage);
            // continue trying with k-1 (tighter) to reduce colors further
            // keep the loop going
            // To speed up, you might initialise next palette run with mutated versions of best, but keep simple
            continue;
        } else {
            // failed for this k: stop and return last valid solution (if any)
            if (!best_solution.empty()) {
                return best_solution;
            } else {
                // never found a valid colouring for any tried k; return the best we have with minimal fitness
                // find minimal fitness individual across population:
                const Individual *min_ind = &population.front();
                for (const auto &ind : population) {
                    if (ind.fitness < min_ind->fitness) min_ind = &ind;
                }
                return min_ind->colours;
            }
        }
    } // end palette loop

    // If loop finishes (palette_k reached 0), return best_solution if any, else empty
    if (!best_solution.empty()) return best_solution;
    // fallback: return a trivial colouring (all zeros)
    return std::vector<int>(n, 0);
}

// Snapshot writer helper
static void write_snapshot_line(std::ofstream &out, const std::vector<int> &colours) {
    for (std::size_t i = 0; i < colours.size(); ++i) {
        if (i) out.put(' ');
        out << colours[i];
    }
    out.put('\n');
}

std::vector<int> colour_with_genetic_snapshots(const Graph &graph,
                                               const std::string &snapshots_path,
                                               int population_size,
                                               int max_generations,
                                               double mutation_rate) {
    const int n = graph.vertex_count;
    if (n == 0) return {};

    std::ofstream out(snapshots_path);
    if (!out.is_open()) {
        throw std::runtime_error("Failed to open Genetic snapshots file: " + snapshots_path);
    }

    population_size = std::max(6, population_size | 1);
    std::mt19937 rng(std::random_device{}());

    int maxdeg = max_degree(graph);
    int start_palette = std::min(maxdeg + 1, std::max(50, (maxdeg + 1)));
    const int HARD_CAP = std::max(200, start_palette);
    if (start_palette > HARD_CAP) start_palette = HARD_CAP;

    std::vector<int> best_solution;
    long long best_fitness_overall = std::numeric_limits<long long>::max();

    for (int palette_k = start_palette; palette_k >= 1; --palette_k) {
        std::uniform_int_distribution<int> colour_dist(0, palette_k - 1);

        std::vector<Individual> population(population_size);
        for (auto &ind : population) {
            ind.colours.resize(n);
            for (int v = 0; v < n; ++v) ind.colours[v] = colour_dist(rng);
            ind.colours = greedy_repair_fixed_k(graph, ind.colours, palette_k);
            evaluate(ind, graph);
        }

        // record best of initial population
        Individual best = population.front();
        for (const auto &ind : population) if (ind.fitness < best.fitness) best = ind;
        if (best.fitness < best_fitness_overall) {
            best_fitness_overall = best.fitness;
            best_solution = best.colours;
            write_snapshot_line(out, best_solution);
        }

        bool found_valid = (best.conflicts == 0);
        std::vector<Individual> next_pop;
        next_pop.reserve(population_size);

        for (int gen = 0; gen < max_generations && !found_valid; ++gen) {
            std::sort(population.begin(), population.end(), [](const Individual &a, const Individual &b){return a.fitness < b.fitness;});
            if (population.front().fitness < best.fitness) best = population.front();
            if (best.fitness < best_fitness_overall) {
                best_fitness_overall = best.fitness;
                best_solution = best.colours;
                write_snapshot_line(out, best_solution);
            }
            if (best.conflicts == 0) { found_valid = true; break; }

            next_pop.clear();
            int elites = std::min(2, population_size);
            for (int i = 0; i < elites; ++i) next_pop.push_back(population[i]);
            while (static_cast<int>(next_pop.size()) < population_size) {
                const Individual &pa = tournament_select(population, rng);
                const Individual &pb = tournament_select(population, rng);
                Individual child = crossover(pa, pb, rng, palette_k);
                mutate(child, rng, palette_k, mutation_rate);
                child.colours = greedy_repair_fixed_k(graph, child.colours, palette_k);
                evaluate(child, graph);
                next_pop.push_back(std::move(child));
            }
            population.swap(next_pop);
        }

        for (const auto &ind : population) if (ind.fitness < best.fitness) best = ind;
        if (best.fitness < best_fitness_overall) {
            best_fitness_overall = best.fitness;
            best_solution = best.colours;
            write_snapshot_line(out, best_solution);
        }

        if (best.conflicts == 0) {
            continue; // try smaller palette
        } else {
            if (!best_solution.empty()) return best_solution;
            const Individual *min_ind = &population.front();
            for (const auto &ind : population) if (ind.fitness < min_ind->fitness) min_ind = &ind;
            write_snapshot_line(out, min_ind->colours);
            return min_ind->colours;
        }
    }

    if (!best_solution.empty()) {
        write_snapshot_line(out, best_solution);
        return best_solution;
    }
    std::vector<int> trivial(n, 0);
    write_snapshot_line(out, trivial);
    return trivial;
}

} // namespace graph_colouring
