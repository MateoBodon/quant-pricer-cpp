#include "quant/risk.hpp"
#include "quant/math.hpp"

#include <pcg_random.hpp>

#include <algorithm>
#include <cmath>
#include <random>

namespace quant::risk {

VarEs var_cvar_from_pnl(const std::vector<double>& pnl, double alpha) {
    if (pnl.empty()) return {0.0, 0.0};
    std::vector<double> sorted = pnl;
    std::sort(sorted.begin(), sorted.end());
    const std::size_t idx = static_cast<std::size_t>(std::floor((1.0 - alpha) * sorted.size()));
    const double var = -sorted[idx];
    double es_sum = 0.0;
    for (std::size_t i = 0; i <= idx; ++i) es_sum += -sorted[i];
    const double cvar = es_sum / static_cast<double>(idx + 1);
    return {var, cvar};
}

VarEs var_cvar_gbm(double spot,
                   double mu,
                   double sigma,
                   double horizon_years,
                   double position,
                   unsigned long num_sims,
                   unsigned long seed,
                   double alpha) {
    pcg64 rng(seed ? seed : 0xDEADBEEF);
    std::normal_distribution<double> normal(0.0, 1.0);
    std::vector<double> pnl;
    pnl.reserve(num_sims);
    const double drift = (mu - 0.5 * sigma * sigma) * horizon_years;
    const double vol = sigma * std::sqrt(horizon_years);
    for (unsigned long i = 0; i < num_sims; ++i) {
        double z = normal(rng);
        double S1 = spot * std::exp(drift + vol * z);
        double pl = position * (S1 - spot);
        pnl.push_back(pl);
    }
    return var_cvar_from_pnl(pnl, alpha);
}

} // namespace quant::risk


