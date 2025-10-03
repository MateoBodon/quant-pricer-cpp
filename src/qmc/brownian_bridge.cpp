#include "quant/qmc/brownian_bridge.hpp"

#include <algorithm>
#include <cmath>
#include <stdexcept>

namespace quant::qmc {

BrownianBridge::BrownianBridge(std::size_t steps, double maturity)
    : size_(steps),
      maturity_(maturity),
      times_(steps),
      bridge_index_(steps),
      left_index_(steps),
      right_index_(steps),
      left_weight_(steps),
      right_weight_(steps),
      std_dev_(steps) {
    if (steps == 0) {
        throw std::invalid_argument("BrownianBridge: number of steps must be positive");
    }
    if (maturity <= 0.0) {
        throw std::invalid_argument("BrownianBridge: maturity must be positive");
    }

    const double dt = maturity_ / static_cast<double>(steps);
    for (std::size_t i = 0; i < steps; ++i) {
        times_[i] = dt * static_cast<double>(i + 1);
    }

    initialize();
}

void BrownianBridge::initialize() {
    workspace_.assign(size_, 0.0);

    std::vector<std::size_t> map(size_, 0);

    bridge_index_[0] = size_ - 1;
    left_index_[0] = 0;
    right_index_[0] = size_ - 1;
    std_dev_[0] = std::sqrt(times_[size_ - 1]);
    left_weight_[0] = 0.0;
    right_weight_[0] = 0.0;
    map[size_ - 1] = 1;

    std::size_t j = 0;
    for (std::size_t i = 1; i < size_; ++i) {
        while (map[j] != 0) {
            ++j;
        }
        std::size_t k = j;
        while (map[k] == 0) {
            ++k;
        }
        std::size_t l = j + ((k - j) >> 1);
        map[l] = i + 1;

        bridge_index_[i] = l;
        left_index_[i] = j;
        right_index_[i] = k;

        const double t_l = times_[l];
        const double t_k = times_[k];
        const double t_left = (j == 0) ? 0.0 : times_[j - 1];

        if (j != 0) {
            const double denom = t_k - t_left;
            left_weight_[i] = (t_k - t_l) / denom;
            right_weight_[i] = (t_l - t_left) / denom;
            std_dev_[i] = std::sqrt((t_l - t_left) * (t_k - t_l) / denom);
        } else {
            left_weight_[i] = (t_k - t_l) / t_k;
            right_weight_[i] = t_l / t_k;
            std_dev_[i] = std::sqrt(t_l * (t_k - t_l) / t_k);
        }

        j = k + 1;
        if (j >= size_) {
            j = 0;
        }
    }
}

void BrownianBridge::transform(const double* normals, double* increments) const {
    if (size_ == 0) {
        return;
    }

    std::vector<double>& path = workspace_;
    std::fill(path.begin(), path.end(), 0.0);

    path[bridge_index_[0]] = std_dev_[0] * normals[0];
    for (std::size_t i = 1; i < size_; ++i) {
        const std::size_t j = left_index_[i];
        const std::size_t k = right_index_[i];
        const std::size_t l = bridge_index_[i];

        double mean = 0.0;
        if (j != 0) {
            mean = left_weight_[i] * path[j - 1] + right_weight_[i] * path[k];
        } else {
            mean = right_weight_[i] * path[k];
        }
        path[l] = mean + std_dev_[i] * normals[i];
    }

    double previous = 0.0;
    for (std::size_t i = 0; i < size_; ++i) {
        const double current = path[i];
        increments[i] = current - previous;
        previous = current;
    }
}

} // namespace quant::qmc
