#include <algorithm>
#include <cmath>
#include <gtest/gtest.h>

#include "quant/grid_utils.hpp"

using namespace quant;

TEST(GridUtils, BuildSpaceGridAnchorsStrike) {
    grid_utils::StretchedGridParams params{
        .nodes = 21, .lower = 0.0, .upper = 400.0, .anchor = 250.0, .stretch = 3.0, .log_space = false};
    auto grid = grid_utils::build_space_grid(params);
    ASSERT_EQ(grid.coordinate.size(), static_cast<std::size_t>(params.nodes));
    ASSERT_EQ(grid.spot.size(), static_cast<std::size_t>(params.nodes));
    for (std::size_t i = 1; i < grid.coordinate.size(); ++i) {
        EXPECT_GT(grid.coordinate[i], grid.coordinate[i - 1]);
    }
    auto it = std::min_element(grid.spot.begin(), grid.spot.end(), [&](double a, double b) {
        return std::abs(a - params.anchor) < std::abs(b - params.anchor);
    });
    ASSERT_NE(it, grid.spot.end());
    EXPECT_NEAR(*it, params.anchor, 25.0);
}

TEST(GridUtils, DirichletBoundaryMatchesAnalytic) {
    grid_utils::PayoffBoundaryParams p{
        .type = OptionType::Put, .strike = 100.0, .rate = 0.05, .dividend = 0.02, .tau = 0.5};
    double lower = grid_utils::dirichlet_boundary(p, 40.0, true);
    double upper = grid_utils::dirichlet_boundary(p, 260.0, false);
    EXPECT_GT(lower, 0.0);
    EXPECT_NEAR(upper, 0.0, 1e-12);
}
