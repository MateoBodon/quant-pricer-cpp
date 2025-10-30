#include <gtest/gtest.h>

#include "quant/heston.hpp"
#include "quant/math.hpp"

namespace {

quant::heston::McParams make_mc_params(const quant::heston::MarketParams& mkt,
                                       const quant::heston::Params& h,
                                       std::uint64_t paths,
                                       std::uint64_t seed,
                                       int steps) {
    quant::heston::McParams mc{mkt, h, paths, seed, steps, true};
    mc.rng = quant::rng::Mode::Counter;
    mc.scheme = quant::heston::McParams::Scheme::QE;
    return mc;
}

void expect_mc_within_ci(const quant::heston::McResult& mc,
                         double reference,
                         double z_threshold = quant::math::kZ95) {
    ASSERT_GT(mc.std_error, 0.0);
    const double diff = std::abs(mc.price - reference);
    EXPECT_LE(diff, z_threshold * mc.std_error);
}

} // namespace

TEST(HestonMc, StandardParametersMatchesCalibrationReference) {
    const quant::heston::Params h{1.5, 0.04, 0.5, -0.5, 0.04};
    const quant::heston::MarketParams mkt{100.0, 100.0, 0.01, 0.0, 1.0};
    const double reference = 8.83129;
    const auto mc_params = make_mc_params(mkt, h, 120000, 2025, 96);
    const auto mc = quant::heston::call_qe_mc(mc_params);
    EXPECT_GT(mc.price, 0.0);
    expect_mc_within_ci(mc, reference);
}

TEST(HestonMc, NearFellerBoundaryStable) {
    const quant::heston::Params h{0.5, 0.04, 0.2, -0.3, 0.04};
    const quant::heston::MarketParams mkt{120.0, 110.0, 0.015, 0.005, 2.0};
    const double reference = 19.4605;
    const auto mc_params = make_mc_params(mkt, h, 180000, 314159, 128);
    const auto mc = quant::heston::call_qe_mc(mc_params);
    EXPECT_GT(mc.price, 0.0);
    expect_mc_within_ci(mc, reference);
}

TEST(HestonMc, HighCorrelationScenario) {
    const quant::heston::Params h{1.2, 0.03, 0.4, 0.85, 0.05};
    const quant::heston::MarketParams mkt{90.0, 80.0, 0.02, 0.0, 1.5};
    const double reference = 11.8734;
    const auto mc_params = make_mc_params(mkt, h, 180000, 424242, 120);
    const auto mc = quant::heston::call_qe_mc(mc_params);
    EXPECT_GT(mc.price, 0.0);
    expect_mc_within_ci(mc, reference);
}
