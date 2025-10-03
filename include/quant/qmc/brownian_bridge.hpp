/// Brownian bridge mapping for quasi Monte Carlo Brownian paths
#pragma once

#include <cstddef>
#include <vector>

namespace quant::qmc {

class BrownianBridge {
public:
    BrownianBridge(std::size_t steps, double maturity);

    std::size_t size() const { return size_; }

    void transform(const double* normals, double* increments) const;

private:
    void initialize();

    std::size_t size_{};
    double maturity_{};
    std::vector<double> times_;
    std::vector<std::size_t> bridge_index_;
    std::vector<std::size_t> left_index_;
    std::vector<std::size_t> right_index_;
    std::vector<double> left_weight_;
    std::vector<double> right_weight_;
    std::vector<double> std_dev_;
    mutable std::vector<double> workspace_;
};

} // namespace quant::qmc
