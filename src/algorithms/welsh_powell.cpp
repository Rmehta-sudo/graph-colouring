#include "welsh_powell.h"
#include <algorithm>
#include <vector>

namespace graph_colouring {

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

} // namespace graph_colouring
