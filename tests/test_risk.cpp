#include <gtest/gtest.h>

#include "quant/risk.hpp"
#include "quant/math.hpp"

#include <cmath>
#include <vector>
#include <limits>

namespace {

double chi_square_tail_df1(double x) {
    // Closed form tail for Chi-square(df=1)
    return std::erfc(std::sqrt(std::max(0.0, x)) / std::sqrt(2.0));
}

double chi_square_tail_df2(double x) {
    return std::exp(-0.5 * x);
}

} // namespace

TEST(RiskBacktest, KupiecPValuesBoundedAndAccurate) {
    // Construct exception sequence with alpha = 0.95, T = 100, N = 5 (on target)
    const double alpha = 0.95;
    std::vector<int> exceptions(100, 0);
    for (int idx : {10, 30, 50, 70, 90}) {
        exceptions[idx] = 1;
    }

    auto stats = quant::risk::kupiec_christoffersen(exceptions, alpha);

    // Validate Kupiec tail against closed form (df = 1)
    const double expected_lr_pof = stats.lr_pof;
    const double expected_pof_tail = chi_square_tail_df1(expected_lr_pof);
    EXPECT_NEAR(stats.p_pof, expected_pof_tail, 1e-12);

    // Independence LR has df = 1 as well
    const double expected_lr_ind = stats.lr_ind;
    const double expected_ind_tail = chi_square_tail_df1(expected_lr_ind);
    EXPECT_NEAR(stats.p_ind, expected_ind_tail, 1e-12);

    // Combined coverage has df = 2
    const double expected_lr_cc = stats.lr_cc;
    const double expected_cc_tail = chi_square_tail_df2(expected_lr_cc);
    EXPECT_NEAR(stats.p_cc, expected_cc_tail, 1e-12);

    // All p-values must lie inside [0,1]
    EXPECT_GE(stats.p_pof, 0.0);
    EXPECT_LE(stats.p_pof, 1.0);
    EXPECT_GE(stats.p_ind, 0.0);
    EXPECT_LE(stats.p_ind, 1.0);
    EXPECT_GE(stats.p_cc, 0.0);
    EXPECT_LE(stats.p_cc, 1.0);
}

TEST(RiskBacktest, StudentTRequiresFiniteVariance) {
    const double mu = 0.0;
    const double sigma = 0.2;
    const double horizon = 1.0 / 252.0;
    const double position = 1.0;
    const unsigned long sims = 1000;
    const unsigned long seed = 42;
    const double alpha = 0.99;

    EXPECT_THROW(
        quant::risk::var_cvar_t(mu, sigma, 2.0, horizon, position, sims, seed, alpha),
        std::invalid_argument);

    EXPECT_THROW(
        quant::risk::var_cvar_t(mu, sigma, 1.5, horizon, position, sims, seed, alpha),
        std::invalid_argument);

    EXPECT_NO_THROW(
        quant::risk::var_cvar_t(mu, sigma, 5.0, horizon, position, sims, seed, alpha));
}

TEST(RiskBacktest, GbmVarMatchesAnalyticQuantile) {
    const double spot = 100.0;
    const double mu = 0.01;
    const double sigma = 0.2;
    const double horizon = 1.0 / 252.0;
    const double position = 1.0;
    const unsigned long sims = 200000;
    const unsigned long seed = 4242;
    const double alpha = 0.99;

    auto stats = quant::risk::var_cvar_gbm(spot, mu, sigma, horizon, position, sims, seed, alpha);

    const double drift = (mu - 0.5 * sigma * sigma) * horizon;
    const double vol_term = sigma * std::sqrt(horizon);
    const double u = 1.0 - alpha;
    const double z = quant::math::inverse_normal_cdf(std::max(std::numeric_limits<double>::min(), u));
    const double st_quantile = spot * std::exp(drift + vol_term * z);
    const double pnl_quantile = position * (st_quantile - spot);
    const double var_expected = -pnl_quantile;

    EXPECT_NEAR(stats.var, var_expected, 0.2);
    EXPECT_GT(stats.cvar, stats.var);
}
