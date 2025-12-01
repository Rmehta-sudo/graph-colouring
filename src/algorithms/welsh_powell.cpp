/**
 * @file welsh_powell.cpp
 * @brief Implementation of Welsh-Powell greedy graph colouring algorithm.
 * 
 * Welsh-Powell sorts vertices by degree and assigns colours greedily.
 * Simple and fast, but may use more colours than DSatur on many graphs.
 */

#include "welsh_powell.h"
#include <algorithm>
#include <vector>
#include <fstream>
#include <stdexcept>
#include <stdexcept>

namespace graph_colouring {

/**
 * @brief Colours a graph using the Welsh-Powell greedy algorithm.
 * 
 * Implementation:
 * 1. Create vertex ordering by descending degree
 * 2. For each uncoloured vertex in order:
 *    a. Assign current colour to this vertex
 *    b. Assign same colour to all subsequent compatible vertices
 *    c. Increment colour counter
 * 
 * @param graph The input graph to colour.
 * @return std::vector<int> Colour assignments (0-indexed).
 */
std::vector<int> colour_with_welsh_powell(const Graph &graph) {
    const int n = graph.vertex_count;
    if (n == 0) return {};

    // colours[u] = assigned colour of vertex u, -1 = uncoloured
    std::vector<int> colour(n, -1);

    // Create ordering of vertices by descending degree
    std::vector<int> order(n);
    for (int i = 0; i < n; i++)
        order[i] = i;

    std::sort(order.begin(), order.end(),
        [&](int a, int b) {
            return graph.adjacency_list[a].size() > graph.adjacency_list[b].size();
        }
    );

    int current_color = 0;

    // Assign colours greedily in sorted order
    for (int i = 0; i < n; i++) {
        int v = order[i];
        if (colour[v] != -1) continue; // already coloured from earlier pass

        colour[v] = current_color;

        // Colour all vertices that can safely take current_color
        for (int j = i + 1; j < n; j++) {
            int u = order[j];
            if (colour[u] == -1) {
                bool conflict = false;
                for (int nb : graph.adjacency_list[u]) {
                    if (colour[nb] == current_color) {
                        conflict = true;
                        break;
                    }
                }
                if (!conflict) {
                    colour[u] = current_color;
                }
            }
        }

        current_color++;
    }

    return colour;
}

std::vector<int> colour_with_welsh_powell_snapshots(const Graph &graph, const std::string &snapshots_path) {
    const int n = graph.vertex_count;
    if (n == 0) return {};

    std::vector<int> colour(n, -1);

    std::vector<int> order(n);
    for (int i = 0; i < n; i++) order[i] = i;
    std::sort(order.begin(), order.end(),
        [&](int a, int b) {
            return graph.adjacency_list[a].size() > graph.adjacency_list[b].size();
        }
    );

    std::ofstream out(snapshots_path);
    if (!out.is_open()) {
        throw std::runtime_error("Failed to open Welsh-Powell snapshots file: " + snapshots_path);
    }
    auto write_snapshot = [&](){
        for (int i = 0; i < n; ++i) {
            if (i) out << ' ';
            out << colour[i];
        }
        out << '\n';
    };

    int current_color = 0;

    for (int i = 0; i < n; i++) {
        int v = order[i];
        if (colour[v] != -1) continue;

        colour[v] = current_color;
        write_snapshot();

        for (int j = i + 1; j < n; j++) {
            int u = order[j];
            if (colour[u] == -1) {
                bool conflict = false;
                for (int nb : graph.adjacency_list[u]) {
                    if (colour[nb] == current_color) {
                        conflict = true;
                        break;
                    }
                }
                if (!conflict) {
                    colour[u] = current_color;
                    write_snapshot();
                }
            }
        }

        current_color++;
    }

    return colour;
}

} // namespace graph_colouring
