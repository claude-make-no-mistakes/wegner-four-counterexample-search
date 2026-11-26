#include <algorithm>
#include <array>
#include <cstdint>
#include <iostream>
#include <sstream>
#include <stdexcept>
#include <string>
#include <vector>

using Mask = std::uint32_t;
using Graph = std::vector<std::vector<int>>;
constexpr int limit = 26;

Mask bit(int u) { return Mask{1} << u; }

Graph parse(const std::string& line) {
    std::istringstream input(line);
    int n;
    std::string rotation;
    if (!(input >> n >> rotation) || n < 4 || n > limit) {
        throw std::runtime_error("invalid ASCII graph header");
    }
    Graph graph(1);
    for (char label : rotation) {
        if (label == ',') {
            graph.emplace_back();
        } else {
            graph.back().push_back(label - 'a');
        }
    }
    if (graph.size() != static_cast<unsigned>(n)) {
        throw std::runtime_error("rotation list has incorrect length");
    }
    for (int u = 0; u < n; ++u) {
        Mask seen = 0;
        if (graph[u].size() < 3 || graph[u].size() > 4) {
            throw std::runtime_error("expected degrees three or four");
        }
        for (int v : graph[u]) {
            if (v < 0 || v >= n || v == u || (seen & bit(v)) ||
                std::find(graph[v].begin(), graph[v].end(), u) == graph[v].end()) {
                throw std::runtime_error("invalid simple undirected graph");
            }
            seen |= bit(v);
        }
    }
    return graph;
}

bool two_sides(const Graph& graph, const std::array<int, 4>& cycle, int length, Mask used) {
    unsigned sides = 0;
    for (int i = 0; i < length; ++i) {
        const auto& row = graph[cycle[i]];
        const int prev = cycle[(i + length - 1) % length];
        const int next = cycle[(i + 1) % length];
        auto edge = std::find(row.begin(), row.end(), prev);
        unsigned side = 1;
        for (unsigned step = 1; step < row.size(); ++step) {
            if (++edge == row.end()) {
                edge = row.begin();
            }
            if (*edge == next) {
                side = 2;
            } else if (!(used & bit(*edge))) {
                sides |= side;
            }
        }
    }
    return sides == 3;
}

std::string separating_cycle(const Graph& graph) {
    std::array<int, 4> cycle{};
    const auto extend = [&](const auto& self, int length, Mask used) -> int {
        for (int v : graph[cycle[length - 1]]) {
            if (v == cycle[0] && length >= 3 && cycle[1] < cycle[length - 1]
                && two_sides(graph, cycle, length, used)) {
                return length;
            }
            if (length < 4 && v > cycle[0] && !(used & bit(v))) {
                cycle[length] = v;
                const int found = self(self, length + 1, used | bit(v));
                if (found != 0) {
                    return found;
                }
            }
        }
        return 0;
    };
    for (unsigned u = 0; u < graph.size(); ++u) {
        cycle[0] = static_cast<int>(u);
        const int found = extend(extend, 1, bit(cycle[0]));
        if (found != 0) {
            std::string result = "S";
            for (int i = 0; i < found; ++i) {
                result += static_cast<char>('a' + cycle[i]);
            }
            return result;
        }
    }
    return {};
}

class Coloring {
public:
    explicit Coloring(const Graph& graph) : n(static_cast<int>(graph.size())) {
        for (int u = 0; u < n; ++u) {
            for (int v : graph[u]) {
                square[u] |= bit(v);
                for (int w : graph[v]) {
                    square[u] |= bit(w);
                }
            }
            square[u] &= ~bit(u);
        }
    }

    std::string solve(int maximum) {
        palette = maximum;
        if (!assign(bit(n) - 1, 0)) {
            return {};
        }
        std::string witness;
        for (int u = 0; u < n; ++u) {
            witness += static_cast<char>('0' + colors[u]);
        }
        return witness;
    }

private:
    int n, palette = 0;
    std::array<Mask, limit> square{}, seen_colors{};
    std::array<int, limit> colors{};

    bool assign(Mask uncolored, int used) {
        if (!uncolored) {
            return true;
        }
        int chosen = -1, best = -1;
        for (Mask left = uncolored; left; left &= left - 1) {
            const int u = __builtin_ctz(left);
            const int saturation = __builtin_popcount(seen_colors[u]);
            if (saturation >= palette) {
                return false;
            }
            const int score = 32 * saturation + __builtin_popcount(square[u] & uncolored);
            if (score > best) {
                chosen = u;
                best = score;
            }
        }
        uncolored ^= bit(chosen);
        Mask allowed = (bit(std::min(palette, used + 1)) - 1) & ~seen_colors[chosen];
        while (allowed) {
            const Mask color = allowed & -allowed;
            allowed ^= color;
            Mask changed = 0;
            for (Mask near = square[chosen] & uncolored; near; near &= near - 1) {
                const int v = __builtin_ctz(near);
                if (!(seen_colors[v] & color)) {
                    seen_colors[v] |= color;
                    changed |= bit(v);
                }
            }
            const int c = __builtin_ctz(color);
            colors[chosen] = c;
            const bool solved = assign(uncolored, std::max(c + 1, used));
            for (; changed; changed &= changed - 1) {
                seen_colors[__builtin_ctz(changed)] ^= color;
            }
            if (solved) {
                return true;
            }
        }
        return false;
    }
};

int main(int argc, char** argv) {
    const bool skip_separators = argc == 1;
    if (!skip_separators && (argc != 2 || std::string(argv[1]) != "--all")) {
        std::cerr << "usage: search [--all]\n";
        return 2;
    }
    std::ios::sync_with_stdio(false);
    std::string line;
    try {
        while (std::getline(std::cin, line)) {
            if (line.empty()) {
                continue;
            }
            const auto graph = parse(line);
            auto witness = skip_separators ? separating_cycle(graph) : std::string{};
            if (witness.empty()) {
                Coloring coloring(graph);
                witness = coloring.solve(8);
                if (witness.empty()) {
                    witness = coloring.solve(9);
                }
            }
            std::cout << line << ' ' << (witness.empty() ? "FAIL" : witness) << '\n';
        }
    } catch (const std::exception& ex) {
        std::cerr << ex.what() << '\n';
        return 1;
    }
}
