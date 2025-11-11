#include "quant/black_scholes.hpp"
#include "quant/mc.hpp"
#include "quant/pde.hpp"
#include <gtest/gtest.h>

// Verify that supplying constant schedules matches scalar params (MC and PDE)

TEST(TermStructures, McConstantScheduleMatchesScalar) {
    quant::mc::McParams a{100.0, 100.0, 0.02, 0.01, 0.20, 1.0, 200000, 4242, true, true};
    auto base = quant::mc::price_european_call(a);

    quant::PiecewiseConstant r{{0.25, 0.50, 1.0}, {0.02, 0.02, 0.02}};
    quant::PiecewiseConstant q{{0.25, 0.50, 1.0}, {0.01, 0.01, 0.01}};
    quant::PiecewiseConstant v{{0.25, 0.50, 1.0}, {0.20, 0.20, 0.20}};
    a.rate_schedule = r;
    a.dividend_schedule = q;
    a.vol_schedule = v;
    auto sch = quant::mc::price_european_call(a);
    EXPECT_NEAR(base.estimate.value, sch.estimate.value,
                3.0 * sch.estimate.std_error + 3.0 * base.estimate.std_error);
}

TEST(TermStructures, PdeConstantScheduleMatchesScalar) {
    quant::pde::PdeParams p{.spot = 100.0,
                            .strike = 100.0,
                            .rate = 0.02,
                            .dividend = 0.01,
                            .vol = 0.20,
                            .time = 1.0,
                            .type = quant::OptionType::Call,
                            .grid = quant::pde::GridSpec{241, 240, 4.0, 2.0},
                            .log_space = true,
                            .upper_boundary = quant::pde::PdeParams::UpperBoundary::Neumann,
                            .compute_theta = false,
                            .use_rannacher = true};
    auto base = quant::pde::price_crank_nicolson(p);

    quant::PiecewiseConstant r{{0.25, 0.50, 1.0}, {0.02, 0.02, 0.02}};
    quant::PiecewiseConstant q{{0.25, 0.50, 1.0}, {0.01, 0.01, 0.01}};
    quant::PiecewiseConstant v{{0.25, 0.50, 1.0}, {0.20, 0.20, 0.20}};
    p.rate_schedule = r;
    p.dividend_schedule = q;
    p.vol_schedule = v;
    auto sch = quant::pde::price_crank_nicolson(p);
    EXPECT_NEAR(base.price, sch.price, 5e-3);
}

TEST(TermStructures, McGreeksConstantScheduleMatchesScalar) {
    quant::mc::McParams base{.spot = 100.0,
                             .strike = 100.0,
                             .rate = 0.02,
                             .dividend = 0.01,
                             .vol = 0.20,
                             .time = 1.0,
                             .num_paths = 300000,
                             .seed = 98765,
                             .antithetic = true,
                             .control_variate = true,
                             .qmc = quant::mc::McParams::Qmc::None,
                             .bridge = quant::mc::McParams::Bridge::None,
                             .num_steps = 1};

    auto greeks_scalar = quant::mc::greeks_european_call(base);

    quant::PiecewiseConstant r{{0.25, 0.50, 1.0}, {0.02, 0.02, 0.02}};
    quant::PiecewiseConstant q{{0.25, 0.50, 1.0}, {0.01, 0.01, 0.01}};
    quant::PiecewiseConstant v{{0.25, 0.50, 1.0}, {0.20, 0.20, 0.20}};

    auto sched = base;
    sched.rate_schedule = r;
    sched.dividend_schedule = q;
    sched.vol_schedule = v;
    auto greeks_sched = quant::mc::greeks_european_call(sched);

    const double delta_ref =
        quant::bs::delta_call(base.spot, base.strike, base.rate, base.dividend, base.vol, base.time);
    const double vega_ref =
        quant::bs::vega(base.spot, base.strike, base.rate, base.dividend, base.vol, base.time);
    const double gamma_ref =
        quant::bs::gamma(base.spot, base.strike, base.rate, base.dividend, base.vol, base.time);

    EXPECT_NEAR(greeks_sched.delta.value, delta_ref, 4.0 * greeks_sched.delta.std_error);
    EXPECT_NEAR(greeks_sched.vega.value, vega_ref, 4.0 * greeks_sched.vega.std_error);
    EXPECT_NEAR(greeks_sched.gamma_lrm.value, gamma_ref, 4.0 * greeks_sched.gamma_lrm.std_error);
    EXPECT_NEAR(greeks_sched.gamma_mixed.value, gamma_ref, 4.0 * greeks_sched.gamma_mixed.std_error);

    EXPECT_NEAR(greeks_sched.delta.value, greeks_scalar.delta.value, 4.0 * greeks_sched.delta.std_error);
}
