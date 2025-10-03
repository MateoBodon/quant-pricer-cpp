/// Sobol quasi-random sequence (Joe–Kuo direction numbers with optional scramble)
#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <vector>

namespace quant::qmc {

class SobolSequence {
public:
    static constexpr std::size_t kMaxSupportedDimension = 64;
    static constexpr std::size_t kMaxBits = 64;

    SobolSequence(std::size_t dimension,
                  bool scrambled = false,
                  std::uint64_t seed = 0);

    std::size_t dimension() const { return dimension_; }

    void generate(std::uint64_t index, double* out) const;
    std::vector<double> generate(std::uint64_t index) const;

private:
    struct DirectionRow {
        std::array<std::uint64_t, kMaxBits> values{};
    };

    std::size_t dimension_;
    std::vector<DirectionRow> directions_;
    std::vector<std::uint64_t> scramble_; // digital shift per dimension
};

} // namespace quant::qmc

