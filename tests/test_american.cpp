#include <cmath>
#include <gtest/gtest.h>

#include "quant/american.hpp"
#include "quant/barrier.hpp"

using namespace quant;

TEST(AmericanFast, PsorMatchesBinomial) {
    american::Params base{
        .spot = 100.0,
        .strike = 100.0,
        .rate = 0.05,
        .dividend = 0.02,
        .vol = 0.25,
        .time = 1.0,
        .type = OptionType::Put
    };
    double binom = american::price_binomial_crr(base, 256);

    american::PsorParams psor{
        .base = base,
        .grid = quant::pde::GridSpec{161, 160, 4.0, 0.0},
        .log_space = true,
        .upper_boundary = quant::pde::PdeParams::UpperBoundary::Neumann,
        .stretch = 2.0,
        .omega = 1.5,
        .max_iterations = 6000,
        .tolerance = 2e-8,
        .use_rannacher = true
    };
    american::PsorResult psor_res = american::price_psor(psor);
    EXPECT_NEAR(psor_res.price, binom, 5e-3);
    EXPECT_GT(psor_res.total_iterations, 0);
}

TEST(AmericanFast, LsmcConsistentWithPsorSmallGrid) {
    american::Params base{
        .spot = 95.0,
        .strike = 100.0,
        .rate = 0.035,
        .dividend = 0.01,
        .vol = 0.22,
        .time = 1.0,
        .type = OptionType::Put
    };

    american::PsorParams psor{
        .base = base,
        .grid = quant::pde::GridSpec{121, 120, 4.0, 0.0},
        .log_space = true,
        .upper_boundary = quant::pde::PdeParams::UpperBoundary::Neumann,
        .stretch = 1.8,
        .omega = 1.45,
        .max_iterations = 4000,
        .tolerance = 5e-8,
        .use_rannacher = true
    };
    auto psor_res = american::price_psor(psor);

    american::LsmcParams lsmc{
        .base = base,
        .num_paths = 8000,
        .seed = 20251030ULL,
        .num_steps = 40,
        .antithetic = true,
        .ridge_lambda = 0.0,
        .itm_moneyness_eps = 0.0,
        .min_itm = 0
    };
    auto lsmc_res = american::price_lsmc(lsmc);

    ASSERT_FALSE(lsmc_res.diagnostics.itm_counts.empty());
    EXPECT_EQ(lsmc_res.diagnostics.itm_counts.size(), lsmc_res.diagnostics.condition_numbers.size());
    double diff = std::abs(lsmc_res.price - psor_res.price);
    ASSERT_GT(lsmc_res.std_error, 0.0);
    double sigma = diff / lsmc_res.std_error;
    EXPECT_LT(sigma, 3.0);
    EXPECT_LT(diff, 3.0 * lsmc_res.std_error + 7e-3);
    double max_cond = 0.0;
    for (double c : lsmc_res.diagnostics.condition_numbers) {
        if (std::isfinite(c)) {
            max_cond = std::max(max_cond, c);
        }
    }
    EXPECT_GT(max_cond, 0.0);
}

TEST(AmericanSlow, LsmcMatchesPsorWithinSe) {
    american::Params base{
        .spot = 90.0,
        .strike = 100.0,
        .rate = 0.03,
        .dividend = 0.01,
        .vol = 0.2,
        .time = 1.0,
        .type = OptionType::Put
    };

    american::PsorParams psor{
        .base = base,
        .grid = quant::pde::GridSpec{181, 180, 4.0, 0.0},
        .log_space = true,
        .upper_boundary = quant::pde::PdeParams::UpperBoundary::Neumann,
        .stretch = 2.0,
        .omega = 1.5,
        .max_iterations = 6000,
        .tolerance = 1e-7,
        .use_rannacher = true
    };
    auto psor_res = american::price_psor(psor);

    american::LsmcParams lsmc{
        .base = base,
        .num_paths = 250000,
        .seed = 20250217ULL,
        .num_steps = 60,
        .antithetic = true,
        .ridge_lambda = 0.0,
        .itm_moneyness_eps = 0.0,
        .min_itm = 0
    };
    auto lsmc_res = american::price_lsmc(lsmc);

    double diff = std::abs(lsmc_res.price - psor_res.price);
    ASSERT_GT(lsmc_res.std_error, 0.0);
    double sigma = diff / lsmc_res.std_error;
    EXPECT_LT(sigma, 4.0);
    EXPECT_LT(diff, 3.0 * lsmc_res.std_error + 5e-3);
    EXPECT_FALSE(lsmc_res.diagnostics.itm_counts.empty());
}
