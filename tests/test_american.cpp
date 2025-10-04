#include <gtest/gtest.h>

#include "quant/american.hpp"
#include "quant/barrier.hpp"

using namespace quant;

TEST(American, PsorMatchesBinomial) {
    american::Params base{
        .spot = 100.0,
        .strike = 100.0,
        .rate = 0.05,
        .dividend = 0.02,
        .vol = 0.25,
        .time = 1.0,
        .type = OptionType::Put
    };
    double binom = american::price_binomial_crr(base, 512);

    american::PsorParams psor{
        .base = base,
        .grid = quant::pde::GridSpec{201, 200, 4.0, 0.0},
        .log_space = true,
        .upper_boundary = quant::pde::PdeParams::UpperBoundary::Neumann,
        .stretch = 2.5,
        .omega = 1.4,
        .max_iterations = 8000,
        .tolerance = 1e-8,
        .use_rannacher = true
    };
    american::PsorResult psor_res = american::price_psor(psor);
    EXPECT_NEAR(psor_res.price, binom, 5e-3);
    EXPECT_GT(psor_res.total_iterations, 0);
}

TEST(American, LsmcMatchesPsorWithinSe) {
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
        .num_paths = 200000,
        .seed = 20250217ULL,
        .num_steps = 50,
        .antithetic = false
    };
    auto lsmc_res = american::price_lsmc(lsmc);

    double diff = std::abs(lsmc_res.price - psor_res.price);
    EXPECT_LT(diff, 3.0 * lsmc_res.std_error + 5e-3);
}

