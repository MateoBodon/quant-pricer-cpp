#include "quant/black_scholes.hpp"
#include "quant/pde.hpp"
#include <cmath>
#include <gtest/gtest.h>
#include <vector>

using namespace quant;

TEST(PDE, PriceMatchesBS_Call) {
    pde::PdeParams pp{.spot = 100.0,
                      .strike = 100.0,
                      .rate = 0.03,
                      .dividend = 0.00,
                      .vol = 0.2,
                      .time = 1.0,
                      .type = quant::OptionType::Call,
                      .grid = pde::GridSpec{201, 200, 4.0}};
    auto res = pde::price_crank_nicolson(pp);
    double bs_price = bs::call_price(pp.spot, pp.strike, pp.rate, pp.dividend, pp.vol, pp.time);
    EXPECT_NEAR(res.price, bs_price, 1e-2);
}

TEST(PDE, PriceMatchesBS_Put) {
    pde::PdeParams pp{.spot = 80.0,
                      .strike = 100.0,
                      .rate = 0.01,
                      .dividend = 0.00,
                      .vol = 0.25,
                      .time = 0.5,
                      .type = quant::OptionType::Put,
                      .grid = pde::GridSpec{201, 200, 4.0}};
    auto res = pde::price_crank_nicolson(pp);
    double bs_price = bs::put_price(pp.spot, pp.strike, pp.rate, pp.dividend, pp.vol, pp.time);
    EXPECT_NEAR(res.price, bs_price, 1.5e-2);
}

TEST(PDE, Convergence) {
    pde::PdeParams base{.spot = 100.0,
                        .strike = 100.0,
                        .rate = 0.02,
                        .dividend = 0.00,
                        .vol = 0.2,
                        .time = 1.0,
                        .type = quant::OptionType::Call,
                        .grid = pde::GridSpec{0, 0, 4.0}};

    double bs_price = bs::call_price(base.spot, base.strike, base.rate, base.dividend, base.vol, base.time);
    auto err = [&](int M, int N) {
        auto pp = base;
        pp.grid = pde::GridSpec{M, N, 4.0};
        auto res = pde::price_crank_nicolson(pp);
        return std::abs(res.price - bs_price);
    };

    double e1 = err(101, 100);
    double e2 = err(201, 200);
    double e3 = err(401, 400);
    EXPECT_GT(e1, e2);
    EXPECT_GT(e2, e3);
}

TEST(PDE, GreeksCloseToBS) {
    pde::PdeParams pp{.spot = 100.0,
                      .strike = 100.0,
                      .rate = 0.02,
                      .dividend = 0.01,
                      .vol = 0.2,
                      .time = 1.0,
                      .type = quant::OptionType::Call,
                      .grid = pde::GridSpec{321, 320, 4.0, 2.5},
                      .log_space = true,
                      .upper_boundary = pde::PdeParams::UpperBoundary::Neumann,
                      .compute_theta = true};

    auto res = pde::price_crank_nicolson(pp);
    double bs_delta = bs::delta_call(pp.spot, pp.strike, pp.rate, pp.dividend, pp.vol, pp.time);
    double bs_gamma = bs::gamma(pp.spot, pp.strike, pp.rate, pp.dividend, pp.vol, pp.time);

    EXPECT_NEAR(res.delta, bs_delta, std::abs(bs_delta) * 0.02);
    EXPECT_NEAR(res.gamma, bs_gamma, std::abs(bs_gamma) * 0.02);
    ASSERT_TRUE(res.theta.has_value());
}

TEST(PDE, BoundaryConditionsMatchAnalytics) {
    pde::PdeParams base{.spot = 110.0,
                        .strike = 100.0,
                        .rate = 0.04,
                        .dividend = 0.01,
                        .vol = 0.22,
                        .time = 0.75,
                        .type = quant::OptionType::Call,
                        .grid = pde::GridSpec{241, 240, 5.0, 1.5},
                        .log_space = true,
                        .upper_boundary = pde::PdeParams::UpperBoundary::Dirichlet,
                        .compute_theta = false,
                        .use_rannacher = true};
    double analytic = bs::call_price(base.spot, base.strike, base.rate, base.dividend, base.vol, base.time);

    auto dirichlet = pde::price_crank_nicolson(base);
    base.upper_boundary = pde::PdeParams::UpperBoundary::Neumann;
    auto neumann = pde::price_crank_nicolson(base);

    EXPECT_NEAR(dirichlet.price, analytic, 5e-3);
    EXPECT_NEAR(neumann.price, analytic, 5e-3);
}

TEST(PDE, RannacherImprovesAccuracy) {
    pde::PdeParams base{.spot = 100.0,
                        .strike = 100.0,
                        .rate = 0.01,
                        .dividend = 0.00,
                        .vol = 0.18,
                        .time = 1.0,
                        .type = quant::OptionType::Put,
                        .grid = pde::GridSpec{51, 10, 4.0, 0.0},
                        .log_space = false,
                        .upper_boundary = pde::PdeParams::UpperBoundary::Dirichlet,
                        .compute_theta = false,
                        .use_rannacher = false};

    double analytic = bs::put_price(base.spot, base.strike, base.rate, base.dividend, base.vol, base.time);
    auto no_rannacher = pde::price_crank_nicolson(base);
    base.use_rannacher = true;
    auto with_rannacher = pde::price_crank_nicolson(base);

    double err_no = std::abs(no_rannacher.price - analytic);
    double err_yes = std::abs(with_rannacher.price - analytic);
    EXPECT_LT(err_yes, err_no);
}

TEST(PDE, SecondOrderSlope) {
    pde::PdeParams base{.spot = 100.0,
                        .strike = 100.0,
                        .rate = 0.02,
                        .dividend = 0.00,
                        .vol = 0.2,
                        .time = 1.0,
                        .type = quant::OptionType::Call,
                        .grid = pde::GridSpec{0, 0, 4.0, 2.0},
                        .log_space = true,
                        .upper_boundary = pde::PdeParams::UpperBoundary::Neumann,
                        .compute_theta = false,
                        .use_rannacher = true};
    const double bs_price =
        bs::call_price(base.spot, base.strike, base.rate, base.dividend, base.vol, base.time);
    std::vector<int> nodes{101, 201, 401};
    std::vector<double> errors;
    for (int m : nodes) {
        auto spec = base;
        spec.grid = pde::GridSpec{m, m - 1, 4.0, 2.0};
        auto res = pde::price_crank_nicolson(spec);
        errors.push_back(std::abs(res.price - bs_price));
    }
    double slope = 0.0;
    if (errors.size() >= 3) {
        double log_e1 = std::log(errors[1] / errors[0]);
        double log_e2 = std::log(errors[2] / errors[1]);
        double log_ratio = std::log(static_cast<double>(nodes[1]) / nodes[0]);
        slope = -log_e1 / log_ratio;
        double slope2 = -log_e2 / std::log(static_cast<double>(nodes[2]) / nodes[1]);
        slope = 0.5 * (slope + slope2);
    }
    EXPECT_NEAR(slope, 2.0, 0.3);
}
