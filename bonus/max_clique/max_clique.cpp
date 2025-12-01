#include <iostream>
#include <vector>
#include <string>
#include <fstream>
#include <sstream>
#include <set>
#include <algorithm>
#include <chrono>

// Simple Graph class using adjacency list
class Graph {
public:
    int n; // Number of vertices
    std::vector<std::vector<int>> adj;

    Graph(int n) : n(n), adj(n) {}

    void add_edge(int u, int v) {
        if (u >= 0 && u < n && v >= 0 && v < n && u != v) {
            adj[u].push_back(v);
            adj[v].push_back(u);
        }
    }
};

// Global variable to store the maximum clique found so far
std::vector<int> max_clique;

// Bron-Kerbosch algorithm with pivoting
void bron_kerbosch(const Graph& g, std::vector<int>& R, std::vector<int>& P, std::vector<int>& X) {
    if (P.empty() && X.empty()) {
        if (R.size() > max_clique.size()) {
            max_clique = R;
        }
        return;
    }

    if (P.empty()) return;

    // Pivot selection: choose u from P U X that maximizes |P \cap N(u)|
    int pivot = -1;
    int max_intersection = -1;

    // Check elements in P
    for (int u : P) {
        int intersection_size = 0;
        for (int v : P) {
            // Check if v is a neighbor of u
            bool is_neighbor = false;
            for (int neighbor : g.adj[u]) {
                if (neighbor == v) {
                    is_neighbor = true;
                    break;
                }
            }
            if (is_neighbor) intersection_size++;
        }
        if (intersection_size > max_intersection) {
            max_intersection = intersection_size;
            pivot = u;
        }
    }
    
    // Check elements in X
    for (int u : X) {
         int intersection_size = 0;
        for (int v : P) {
            // Check if v is a neighbor of u
            bool is_neighbor = false;
            for (int neighbor : g.adj[u]) {
                if (neighbor == v) {
                    is_neighbor = true;
                    break;
                }
            }
            if (is_neighbor) intersection_size++;
        }
        if (intersection_size > max_intersection) {
            max_intersection = intersection_size;
            pivot = u;
        }
    }

    // P \ N(pivot)
    std::vector<int> P_copy = P;
    for (int v : P_copy) {
        bool is_neighbor_of_pivot = false;
        if (pivot != -1) {
             for (int neighbor : g.adj[pivot]) {
                if (neighbor == v) {
                    is_neighbor_of_pivot = true;
                    break;
                }
            }
        }
        
        if (is_neighbor_of_pivot) continue; // Skip neighbors of pivot

        std::vector<int> new_R = R;
        new_R.push_back(v);

        std::vector<int> new_P;
        std::vector<int> new_X;

        // new_P = P intersect N(v)
        for (int p_node : P) {
             for (int neighbor : g.adj[v]) {
                if (neighbor == p_node) {
                    new_P.push_back(p_node);
                    break;
                }
            }
        }

        // new_X = X intersect N(v)
        for (int x_node : X) {
             for (int neighbor : g.adj[v]) {
                if (neighbor == x_node) {
                    new_X.push_back(x_node);
                    break;
                }
            }
        }

        bron_kerbosch(g, new_R, new_P, new_X);

        // P = P \ {v}
        auto it_p = std::find(P.begin(), P.end(), v);
        if (it_p != P.end()) P.erase(it_p);

        // X = X U {v}
        X.push_back(v);
    }
}

// Function to parse DIMACS file
Graph load_dimacs(const std::string& filename) {
    std::ifstream file(filename);
    if (!file.is_open()) {
        std::cerr << "Error: Could not open file " << filename << std::endl;
        exit(1);
    }

    int n = 0;
    int m = 0;
    std::string line;
    Graph g(0);

    while (std::getline(file, line)) {
        if (line.empty() || line[0] == 'c') continue;

        std::stringstream ss(line);
        std::string type;
        ss >> type;

        if (type == "p") {
            std::string format;
            ss >> format >> n >> m;
            g = Graph(n + 1); // 1-based indexing usually, but we'll use 1-based size and 0-based internally if needed, or just map 1->1
            // Actually DIMACS is 1-based. Let's make size n+1 and ignore index 0 to be safe/easy.
        } else if (type == "e") {
            int u, v;
            ss >> u >> v;
            g.add_edge(u, v);
        }
    }
    return g;
}

int main(int argc, char* argv[]) {
    if (argc < 2) {
        std::cerr << "Usage: " << argv[0] << " <input_file>" << std::endl;
        return 1;
    }

    std::string filename = argv[1];
    Graph g = load_dimacs(filename);

    std::vector<int> R;
    std::vector<int> P;
    std::vector<int> X;

    // Initialize P with all vertices (1 to n)
    // Assuming 1-based indexing from DIMACS, vertices are 1..n
    // Our graph size is n+1.
    for (int i = 1; i < g.n; ++i) {
        P.push_back(i);
    }

    auto start = std::chrono::high_resolution_clock::now();
    bron_kerbosch(g, R, P, X);
    auto end = std::chrono::high_resolution_clock::now();
    auto duration = std::chrono::duration_cast<std::chrono::milliseconds>(end - start);

    std::cout << "Max Clique Size: " << max_clique.size() << std::endl;
    std::cout << "Vertices: ";
    for (size_t i = 0; i < max_clique.size(); ++i) {
        std::cout << max_clique[i] << (i == max_clique.size() - 1 ? "" : " ");
    }
    std::cout << std::endl;
    std::cout << "Time (ms): " << duration.count() << std::endl;

    return 0;
}
