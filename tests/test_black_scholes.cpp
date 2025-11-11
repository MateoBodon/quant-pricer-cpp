#include "quant/black_scholes.hpp"
#include <cmath>
#include <gtest/gtest.h>

using namespace quant::bs;

TEST(BlackScholes, KnownValue_Call) {
    // Example parameters (from common BS references)
    double S = 100.0, K = 100.0, r = 0.05, q = 0.0, sigma = 0.2, T = 1.0;
    double price = call_price(S, K, r, q, sigma, T);
    // Known value ~10.4506
    EXPECT_NEAR(price, 10.4506, 1e-4);
}

TEST(BlackScholes, KnownValue_Put) {
    double S = 100.0, K = 100.0, r = 0.05, q = 0.0, sigma = 0.2, T = 1.0;
    double price = put_price(S, K, r, q, sigma, T);
    // Put value ~5.5735
    EXPECT_NEAR(price, 5.5735, 1e-4);
}

TEST(BlackScholes, PutCallParity) {
    double S = 120.0, K = 100.0, r = 0.03, q = 0.01, sigma = 0.25, T = 0.75;
    double c = call_price(S, K, r, q, sigma, T);
    double p = put_price(S, K, r, q, sigma, T);
    double df_r = std::exp(-r * T);
    double df_q = std::exp(-q * T);
    EXPECT_NEAR(c - p, S * df_q - K * df_r, 1e-10);
}

TEST(BlackScholes, EdgeCases_ZeroT) {
    double S = 95.0, K = 100.0, r = 0.02, q = 0.01, sigma = 0.3, T = 0.0;
    EXPECT_DOUBLE_EQ(call_price(S, K, r, q, sigma, T), 0.0);
    EXPECT_DOUBLE_EQ(put_price(S, K, r, q, sigma, T), 5.0);
}

TEST(BlackScholes, EdgeCases_ZeroVol) {
    double S = 130.0, K = 100.0, r = 0.02, q = 0.01, sigma = 0.0, T = 0.5;
    double forward = S * std::exp((r - q) * T);
    double df_r = std::exp(-r * T);
    EXPECT_DOUBLE_EQ(call_price(S, K, r, q, sigma, T), df_r * std::max(0.0, forward - K));
    EXPECT_DOUBLE_EQ(put_price(S, K, r, q, sigma, T), df_r * std::max(0.0, K - forward));
}

TEST(BlackScholesGreeks, SignsAndKnown) {
    double S = 100.0, K = 100.0, r = 0.03, q = 0.01, sigma = 0.2, T = 1.0;

    double dc = delta_call(S, K, r, q, sigma, T);
    double dp = delta_put(S, K, r, q, sigma, T);
    double g = gamma(S, K, r, q, sigma, T);
    double v = vega(S, K, r, q, sigma, T);
    double thc = theta_call(S, K, r, q, sigma, T);
    double thp = theta_put(S, K, r, q, sigma, T);
    double rhc = rho_call(S, K, r, q, sigma, T);
    double rhp = rho_put(S, K, r, q, sigma, T);

    EXPECT_GT(dc, 0.0);
    EXPECT_LT(dp, 0.0);
    EXPECT_GT(g, 0.0);
    EXPECT_GT(v, 0.0);
    // Theta: calls typically negative (time decay). Puts can be negative too depending on params.
    EXPECT_LT(thc, 0.0);
    EXPECT_GT(rhc, 0.0);
    EXPECT_LT(rhp, 0.0);

    // Parity for theta: Theta_C - Theta_P = q S e^{-qT} - r K e^{-rT}
    double df_r = std::exp(-r * T);
    double df_q = std::exp(-q * T);
    EXPECT_NEAR(thc - thp, q * S * df_q - r * K * df_r, 1e-10);

    // Finite-difference sanity for delta and vega
    double epsS = 1e-4;
    double c0 = call_price(S, K, r, q, sigma, T);
    double c_upS = call_price(S + epsS, K, r, q, sigma, T);
    EXPECT_NEAR(dc, (c_upS - c0) / epsS, 2e-3);

    double epsV = 1e-4;
    double c_upV = call_price(S, K, r, q, sigma + epsV, T);
    EXPECT_NEAR(vega(S, K, r, q, sigma, T), (c_upV - c0) / epsV, 2e-3);
}

TEST(BlackScholes, ImpliedVolCallPut) {
    double S = 100.0, K = 100.0, r = 0.01, q = 0.0, T = 1.0, sigma = 0.2;
    double pc = call_price(S, K, r, q, sigma, T);
    double pp = put_price(S, K, r, q, sigma, T);
    double ivc = implied_vol_call(S, K, r, q, T, pc);
    double ivp = implied_vol_put(S, K, r, q, T, pp);
    EXPECT_NEAR(ivc, sigma, 1e-6);
    EXPECT_NEAR(ivp, sigma, 1e-6);
}
