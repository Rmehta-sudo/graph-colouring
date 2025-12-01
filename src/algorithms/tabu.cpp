// TabuCol: Tabu Search metaheuristic for graph colouring
// 
// Strategy:
// 1. Start with a random k-colouring (may have conflicts)
// 2. Iteratively select a conflicting vertex and move it to a colour that
//    minimizes conflicts (even if still > 0)
// 3. Mark the move (vertex, old_colour) as "tabu" for a tenure period to
//    prevent cycling back immediately
// 4. Accept the best non-tabu move; allow tabu moves only if they achieve
//    a new global best (aspiration criterion)
// 5. If zero conflicts achieved, decrease k and restart
// 6. Stop when no feasible k-colouring found within iteration limit

#include "tabu.h"

#include <algorithm>
#include <cmath>
#include <fstream>
#include <limits>
#include <numeric>
#include <random>
#include <stdexcept>
#include <vector>

namespace {

// Count total conflicts in the colouring
int count_conflicts(const graph_colouring::Graph &graph, const std::vector<int> &colours) {
    int conflicts = 0;
    const int n = graph.vertex_count;
    for (int u = 0; u < n; ++u) {
        const int cu = colours[u];
        for (int v : graph.adjacency_list[u]) {
            if (u < v && cu == colours[v]) ++conflicts;
        }
    }
    return conflicts;
}

// Count conflicts involving a specific vertex
int count_conflicts_for_vertex(const graph_colouring::Graph &graph, 
                               const std::vector<int> &colours, 
                               int vertex) {
    int conf = 0;
    const int c = colours[vertex];
    for (int nb : graph.adjacency_list[vertex]) {
        if (colours[nb] == c) ++conf;
    }
    return conf;
}

// Count how many conflicts a vertex would have if assigned to colour c
int count_conflicts_if_colour(const graph_colouring::Graph &graph,
                              const std::vector<int> &colours,
                              int vertex, int c) {
    int conf = 0;
    for (int nb : graph.adjacency_list[vertex]) {
        if (colours[nb] == c) ++conf;
    }
    return conf;
}

// Get all vertices currently in conflict
std::vector<int> get_conflicting_vertices(const graph_colouring::Graph &graph,
                                          const std::vector<int> &colours) {
    std::vector<int> conflicting;
    const int n = graph.vertex_count;
    for (int u = 0; u < n; ++u) {
        if (count_conflicts_for_vertex(graph, colours, u) > 0) {
            conflicting.push_back(u);
        }
    }
    return conflicting;
}

// Get maximum degree in the graph
int max_degree(const graph_colouring::Graph &graph) {
    int m = 0;
    for (const auto &nb : graph.adjacency_list) {
        m = std::max<int>(m, static_cast<int>(nb.size()));
    }
    return m;
}

// Initialize a random k-colouring using greedy approach with randomization
std::vector<int> initialize_colouring(const graph_colouring::Graph &graph, 
                                      int k, std::mt19937 &rng) {
    const int n = graph.vertex_count;
    std::vector<int> colours(n, -1);
    
    // Order vertices by degree (high to low) with some randomization
    std::vector<int> order(n);
    std::iota(order.begin(), order.end(), 0);
    std::sort(order.begin(), order.end(), [&](int a, int b) {
        return graph.adjacency_list[a].size() > graph.adjacency_list[b].size();
    });
    
    std::vector<char> banned(k, 0);
    
    for (int v : order) {
        std::fill(banned.begin(), banned.end(), 0);
        for (int nb : graph.adjacency_list[v]) {
            int c = colours[nb];
            if (c >= 0 && c < k) banned[c] = 1;
        }
        
        // Find available colours
        std::vector<int> available;
        for (int c = 0; c < k; ++c) {
            if (!banned[c]) available.push_back(c);
        }
        
        if (!available.empty()) {
            // Choose randomly among available colours
            std::uniform_int_distribution<int> dist(0, static_cast<int>(available.size()) - 1);
            colours[v] = available[dist(rng)];
        } else {
            // All colours conflict; choose the one with minimum conflicts
            int best_c = 0;
            int best_conf = std::numeric_limits<int>::max();
            for (int c = 0; c < k; ++c) {
                int conf = count_conflicts_if_colour(graph, colours, v, c);
                if (conf < best_conf) {
                    best_conf = conf;
                    best_c = c;
                }
            }
            colours[v] = best_c;
        }
    }
    
    return colours;
}

}  // anonymous namespace

namespace graph_colouring {

std::vector<int> colour_with_tabu(const Graph &graph) {
    // Default parameters tuned for typical DIMACS instances
    // tabu_tenure is often set to 0.6 * |conflicting_vertices| or a fixed value
    int max_iterations = std::max(10000, graph.vertex_count * 100);
    int tabu_tenure = std::max(7, graph.vertex_count / 10);
    return colour_with_tabu(graph, max_iterations, tabu_tenure);
}

std::vector<int> colour_with_tabu(const Graph &graph, int max_iterations, int tabu_tenure) {
    const int n = graph.vertex_count;
    if (n == 0) return {};
    
    std::mt19937 rng(std::random_device{}());
    
    // Start with an upper bound on colours needed
    int start_k = std::min(n, max_degree(graph) + 1);
    
    // Best valid (conflict-free) solution found
    std::vector<int> best_solution;
    
    // Try decreasing k values
    for (int k = start_k; k >= 1; --k) {
        // Initialize colouring with k colours
        std::vector<int> colours = initialize_colouring(graph, k, rng);
        int conflicts = count_conflicts(graph, colours);
        
        // If already conflict-free, record and try smaller k
        if (conflicts == 0) {
            best_solution = colours;
            continue;
        }
        
        // Tabu list: tabu[v][c] = iteration when (v,c) move becomes non-tabu
        // A move (v, old_c -> new_c) makes (v, old_c) tabu
        std::vector<std::vector<int>> tabu(n, std::vector<int>(k, 0));
        
        int best_conflicts_this_k = conflicts;
        std::vector<int> best_colours_this_k = colours;
        
        for (int iter = 1; iter <= max_iterations; ++iter) {
            // Get all conflicting vertices
            std::vector<int> conflicting = get_conflicting_vertices(graph, colours);
            
            if (conflicting.empty()) {
                // Found a valid k-colouring!
                best_solution = colours;
                break;
            }
            
            // Find the best move: (vertex, new_colour, delta_conflicts)
            int best_v = -1;
            int best_new_c = -1;
            int best_delta = std::numeric_limits<int>::max();
            bool best_is_tabu = true;
            
            // Consider all conflicting vertices
            for (int v : conflicting) {
                int old_c = colours[v];
                int old_conf = count_conflicts_for_vertex(graph, colours, v);
                
                // Try all other colours
                for (int new_c = 0; new_c < k; ++new_c) {
                    if (new_c == old_c) continue;
                    
                    int new_conf = count_conflicts_if_colour(graph, colours, v, new_c);
                    int delta = new_conf - old_conf;
                    
                    bool is_tabu = (tabu[v][new_c] > iter);
                    
                    // Aspiration criterion: accept tabu move if it achieves new best
                    int new_total_conflicts = conflicts + delta;
                    bool aspiration = (new_total_conflicts < best_conflicts_this_k);
                    
                    // Select this move if:
                    // 1. It's better than current best move, OR
                    // 2. It's equal but non-tabu beats tabu
                    bool select = false;
                    if (delta < best_delta) {
                        if (!is_tabu || aspiration) select = true;
                    } else if (delta == best_delta && best_is_tabu && !is_tabu) {
                        select = true;
                    }
                    
                    if (select) {
                        best_v = v;
                        best_new_c = new_c;
                        best_delta = delta;
                        best_is_tabu = is_tabu && !aspiration;
                    }
                }
            }
            
            // If no valid move found, break (shouldn't happen with proper implementation)
            if (best_v < 0) break;
            
            // Apply the move
            int old_c = colours[best_v];
            colours[best_v] = best_new_c;
            conflicts += best_delta;
            
            // Update tabu list: forbid moving best_v back to old_c
            tabu[best_v][old_c] = iter + tabu_tenure;
            
            // Track best solution for this k
            if (conflicts < best_conflicts_this_k) {
                best_conflicts_this_k = conflicts;
                best_colours_this_k = colours;
            }
            
            // Check if we found a valid colouring
            if (conflicts == 0) {
                best_solution = colours;
                break;
            }
        }
        
        // If we didn't find a valid k-colouring, stop trying smaller k
        if (conflicts > 0) {
            break;
        }
    }
    
    // Return best valid solution found, or fallback to a greedy solution
    if (!best_solution.empty()) {
        return best_solution;
    }
    
    // Fallback: return a simple greedy colouring
    std::vector<int> fallback(n, 0);
    std::vector<char> used;
    for (int v = 0; v < n; ++v) {
        for (int nb : graph.adjacency_list[v]) {
            int c = fallback[nb];
            if (c >= 0) {
                if (c >= static_cast<int>(used.size())) used.resize(c + 1, 0);
                used[c] = 1;
            }
        }
        int c = 0;
        while (c < static_cast<int>(used.size()) && used[c]) ++c;
        fallback[v] = c;
        std::fill(used.begin(), used.end(), 0);
    }
    return fallback;
}

std::vector<int> colour_with_tabu_snapshots(const Graph &graph, const std::string &snapshots_path) {
    const int n = graph.vertex_count;
    if (n == 0) return {};
    
    std::mt19937 rng(std::random_device{}());
    
    std::ofstream out(snapshots_path);
    if (!out.is_open()) {
        throw std::runtime_error("Failed to open Tabu snapshots file: " + snapshots_path);
    }
    
    auto write_snapshot = [&](const std::vector<int> &colours) {
        for (int i = 0; i < n; ++i) {
            if (i) out << ' ';
            out << colours[i];
        }
        out << '\n';
    };
    
    int start_k = std::min(n, max_degree(graph) + 1);
    int max_iterations = std::max(10000, n * 100);
    int tabu_tenure = std::max(7, n / 10);
    
    std::vector<int> best_solution;
    int best_k = std::numeric_limits<int>::max();
    int global_best_conflicts = std::numeric_limits<int>::max();
    
    for (int k = start_k; k >= 1; --k) {
        std::vector<int> colours = initialize_colouring(graph, k, rng);
        int conflicts = count_conflicts(graph, colours);
        
        // Write initial state for this k
        if (conflicts < global_best_conflicts || 
            (conflicts == 0 && k < best_k)) {
            write_snapshot(colours);
            if (conflicts == 0) {
                best_solution = colours;
                best_k = k;
            }
            if (conflicts < global_best_conflicts) {
                global_best_conflicts = conflicts;
            }
        }
        
        if (conflicts == 0) {
            continue;
        }
        
        std::vector<std::vector<int>> tabu(n, std::vector<int>(k, 0));
        int best_conflicts_this_k = conflicts;
        
        for (int iter = 1; iter <= max_iterations; ++iter) {
            std::vector<int> conflicting = get_conflicting_vertices(graph, colours);
            
            if (conflicting.empty()) {
                best_solution = colours;
                best_k = k;
                write_snapshot(colours);
                break;
            }
            
            int best_v = -1;
            int best_new_c = -1;
            int best_delta = std::numeric_limits<int>::max();
            bool best_is_tabu = true;
            
            for (int v : conflicting) {
                int old_c = colours[v];
                int old_conf = count_conflicts_for_vertex(graph, colours, v);
                
                for (int new_c = 0; new_c < k; ++new_c) {
                    if (new_c == old_c) continue;
                    
                    int new_conf = count_conflicts_if_colour(graph, colours, v, new_c);
                    int delta = new_conf - old_conf;
                    
                    bool is_tabu = (tabu[v][new_c] > iter);
                    int new_total_conflicts = conflicts + delta;
                    bool aspiration = (new_total_conflicts < best_conflicts_this_k);
                    
                    bool select = false;
                    if (delta < best_delta) {
                        if (!is_tabu || aspiration) select = true;
                    } else if (delta == best_delta && best_is_tabu && !is_tabu) {
                        select = true;
                    }
                    
                    if (select) {
                        best_v = v;
                        best_new_c = new_c;
                        best_delta = delta;
                        best_is_tabu = is_tabu && !aspiration;
                    }
                }
            }
            
            if (best_v < 0) break;
            
            int old_c = colours[best_v];
            colours[best_v] = best_new_c;
            conflicts += best_delta;
            
            tabu[best_v][old_c] = iter + tabu_tenure;
            
            // Write snapshot on improvement
            if (conflicts < best_conflicts_this_k) {
                best_conflicts_this_k = conflicts;
                if (conflicts < global_best_conflicts || conflicts == 0) {
                    write_snapshot(colours);
                    global_best_conflicts = std::min(global_best_conflicts, conflicts);
                }
            }
            
            if (conflicts == 0) {
                best_solution = colours;
                best_k = k;
                break;
            }
        }
        
        if (conflicts > 0) {
            break;
        }
    }
    
    // Write final best solution
    if (!best_solution.empty()) {
        write_snapshot(best_solution);
        return best_solution;
    }
    
    // Fallback greedy
    std::vector<int> fallback(n, 0);
    std::vector<char> used;
    for (int v = 0; v < n; ++v) {
        for (int nb : graph.adjacency_list[v]) {
            int c = fallback[nb];
            if (c >= 0) {
                if (c >= static_cast<int>(used.size())) used.resize(c + 1, 0);
                used[c] = 1;
            }
        }
        int c = 0;
        while (c < static_cast<int>(used.size()) && used[c]) ++c;
        fallback[v] = c;
        std::fill(used.begin(), used.end(), 0);
    }
    write_snapshot(fallback);
    return fallback;
}

}  // namespace graph_colouring
