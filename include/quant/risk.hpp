/// Simple VaR/CVaR computation utilities
#pragma once

#include <vector>

namespace quant::risk {

// Compute historical VaR and CVaR (Expected Shortfall) from a vector of P&L samples
// alpha in (0,1), e.g., 0.99 for 99% VaR
struct VarEs {
    double var;
    double cvar;
};

VarEs var_cvar_from_pnl(const std::vector<double>& pnl, double alpha);

// Monte Carlo VaR under GBM for a single asset position
// Returns VaR/CVaR of horizon P&L for position size (positive long)
VarEs var_cvar_gbm(double spot,
                   double mu,
                   double sigma,
                   double horizon_years,
                   double position,
                   unsigned long num_sims,
                   unsigned long seed,
                   double alpha);

// Portfolio VaR/CVaR under joint normal/Gaussian copula (Cholesky)
// mu, sigma, weights have size N; corr is N x N row-major correlation matrix
VarEs var_cvar_portfolio(const std::vector<double>& mu,
                         const std::vector<double>& sigma,
                         const std::vector<double>& corr,
                         const std::vector<double>& weights,
                         double horizon_years,
                         unsigned long num_sims,
                         unsigned long seed,
                         double alpha);

}


