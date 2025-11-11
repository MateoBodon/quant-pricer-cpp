/// Deterministic random number generation utilities
#pragma once

#include <algorithm>
#include <cstdint>
#include <limits>

#include "quant/math.hpp"

namespace quant::rng {

/// RNG mode selection: traditional PRNG or deterministic counter-based
enum class Mode {
    Mt19937, ///< PCG/Mersenne Twister style PRNG (per-thread stateful)
    Counter  ///< Counter-based, reproducible across threading schedules
};

namespace detail {

constexpr std::uint64_t kMixConst1 = 0x9E3779B97F4A7C15ULL;
constexpr std::uint64_t kMixConst2 = 0xBF58476D1CE4E5B9ULL;
constexpr std::uint64_t kMixConst3 = 0x94D049BB133111EBULL;

inline std::uint64_t splitmix64(std::uint64_t x) {
    x += kMixConst1;
    x = (x ^ (x >> 30)) * kMixConst2;
    x = (x ^ (x >> 27)) * kMixConst3;
    x ^= (x >> 31);
    return x;
}

inline std::uint64_t hash_combine(std::uint64_t x, std::uint64_t y) {
    x ^= y + kMixConst1 + (x << 6) + (x >> 2);
    return splitmix64(x);
}

inline double to_unit_interval(std::uint64_t bits) {
    constexpr double kInvPow2_53 = 1.0 / static_cast<double>(1ULL << 53);
    const std::uint64_t mantissa = (bits >> 11); // keep top 53 bits
    double u = (static_cast<double>(mantissa) + 0.5) * kInvPow2_53;
    const double eps = std::numeric_limits<double>::epsilon();
    u = std::clamp(u, eps, 1.0 - eps);
    return u;
}

} // namespace detail

/// Deterministic hash of RNG identifiers -> uniform (0,1)
inline double uniform(std::uint64_t master_seed, std::uint64_t path_id, std::uint32_t step_id,
                      std::uint32_t dim_id, std::uint32_t stream_id) {
    using detail::hash_combine;
    std::uint64_t h = detail::splitmix64(master_seed + detail::kMixConst1);
    h = hash_combine(h, path_id);
    h = hash_combine(h, (static_cast<std::uint64_t>(step_id) << 32) | dim_id);
    h = hash_combine(h, stream_id);
    return detail::to_unit_interval(h);
}

/// Deterministic standard normal draw via inverse CDF transform
inline double normal(std::uint64_t master_seed, std::uint64_t path_id, std::uint32_t step_id,
                     std::uint32_t dim_id, std::uint32_t stream_id) {
    const double u = uniform(master_seed, path_id, step_id, dim_id, stream_id);
    return quant::math::inverse_normal_cdf(u);
}

} // namespace quant::rng
