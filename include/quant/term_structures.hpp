/// Simple piecewise-constant term structures for r(t), q(t), sigma(t)
#pragma once

#include <vector>
#include <stdexcept>
#include <algorithm>

namespace quant {

struct PiecewiseConstant {
    std::vector<double> times;   // strictly increasing, terminal time inclusive
    std::vector<double> values;  // same size as times (value on (t_{i-1}, t_i])

    double value(double t) const {
        if (times.empty() || values.empty() || times.size() != values.size()) {
            throw std::runtime_error("PiecewiseConstant: invalid schedule");
        }
        // Right-closed intervals: value is constant on (t_{i-1}, t_i],
        // and for t <= times.front() we return the first value.
        if (t <= times.front()) return values.front();
        auto it = std::lower_bound(times.begin(), times.end(), t); // first time >= t
        std::size_t idx = static_cast<std::size_t>(std::distance(times.begin(), it));
        if (idx >= values.size()) return values.back();
        return values[idx];
    }
};

} // namespace quant


