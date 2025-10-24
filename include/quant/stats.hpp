/// Streaming statistics utilities
#pragma once

#include <cstdint>
#include <algorithm>

namespace quant::stats {

struct Welford {
    std::uint64_t count{0};
    double mean{0.0};
    double m2{0.0};

    inline void add(double value) {
        ++count;
        const double delta = value - mean;
        mean += delta / static_cast<double>(count);
        const double delta2 = value - mean;
        m2 += delta * delta2;
    }

    inline void merge(const Welford& other) {
        if (other.count == 0) return;
        if (count == 0) { *this = other; return; }
        const double total = static_cast<double>(count + other.count);
        const double delta = other.mean - mean;
        mean += delta * static_cast<double>(other.count) / total;
        m2 += other.m2 + delta * delta * (static_cast<double>(count) * other.count / total);
        count += other.count;
    }

    inline double variance() const {
        return (count > 1) ? m2 / static_cast<double>(count - 1) : 0.0;
    }
};

} // namespace quant::stats


