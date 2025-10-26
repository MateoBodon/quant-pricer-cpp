#include "quant/multi.hpp"

#include <algorithm>
#include <cmath>
#include <random>
#include <stdexcept>
#include <vector>
#include "quant/stats.hpp"

#include <pcg_random.hpp>

namespace quant::multi {

static std::vector<double> cholesky_lower(const std::vector<double>& corr, std::size_t n) {
    std::vector<double> L(corr);
    for (std::size_t i = 0; i < n; ++i) {
        for (std::size_t j = 0; j <= i; ++j) {
            double sum = L[i*n + j];
            for (std::size_t k = 0; k < j; ++k) sum -= L[i*n + k] * L[j*n + k];
            if (i == j) {
                L[i*n + j] = (sum > 0.0) ? std::sqrt(sum) : 0.0;
            } else {
                L[i*n + j] = (L[j*n + j] > 0.0) ? (sum / L[j*n + j]) : 0.0;
            }
        }
        for (std::size_t j = i + 1; j < n; ++j) L[i*n + j] = 0.0;
    }
    return L;
}

McStat basket_european_call_mc(const BasketMcParams& p) {
    const std::size_t n = p.spots.size();
    if (n == 0 || p.vols.size() != n || p.dividends.size() != n || p.weights.size() != n) {
        throw std::invalid_argument("BasketMcParams: dimension mismatch");
    }
    if (p.corr.size() != n * n) throw std::invalid_argument("BasketMcParams: corr size mismatch");
    auto L = cholesky_lower(p.corr, n);
    pcg64 rng(p.seed ? p.seed : 0xCAFEBABEULL);
    std::normal_distribution<double> normal(0.0, 1.0);
  const double dt = p.time;
  const double disc = std::exp(-p.rate * p.time);
  quant::stats::Welford acc;
  std::vector<double> z(n), y(n);
  for (std::uint64_t i = 0; i < p.num_paths; ++i) {
        for (std::size_t k = 0; k < n; ++k) z[k] = normal(rng);
        for (std::size_t irow = 0; irow < n; ++irow) {
            double v = 0.0; for (std::size_t k = 0; k <= irow; ++k) v += L[irow*n + k] * z[k];
            y[irow] = v;
        }
        double basket = 0.0;
        for (std::size_t k = 0; k < n; ++k) {
            const double drift = (p.rate - p.dividends[k] - 0.5 * p.vols[k] * p.vols[k]) * dt;
            const double S = p.spots[k] * std::exp(drift + p.vols[k] * std::sqrt(dt) * y[k]);
            basket += p.weights[k] * S;
        }
        const double payoff = std::max(0.0, basket - p.strike);
    const double pv = disc * payoff;
    acc.add(pv);
  }
  double value = acc.mean;
  double var = acc.variance();
  double se = (acc.count > 0) ? std::sqrt(std::max(0.0, var / static_cast<double>(acc.count))) : 0.0;
  return {value, se};
}

McStat merton_call_mc(const MertonParams& p) {
    pcg64 rng(p.seed ? p.seed : 0xDEADC0DEULL);
    std::normal_distribution<double> normal(0.0, 1.0);
    std::poisson_distribution<unsigned> pois(p.lambda * p.time);
  const double disc = std::exp(-p.rate * p.time);
  quant::stats::Welford acc;
  for (std::uint64_t i = 0; i < p.num_paths; ++i) {
        unsigned N = pois(rng);
        double jump_sum = 0.0;
        for (unsigned j = 0; j < N; ++j) {
            double J = p.muJ + p.sigmaJ * normal(rng);
            jump_sum += J;
        }
        const double drift = (p.rate - p.dividend - 0.5 * p.vol * p.vol - p.lambda * (std::exp(p.muJ + 0.5 * p.sigmaJ * p.sigmaJ) - 1.0)) * p.time;
        const double diff = p.vol * std::sqrt(p.time) * normal(rng);
        const double ST = p.spot * std::exp(drift + diff + jump_sum);
        const double payoff = std::max(0.0, ST - p.strike);
    const double pv = disc * payoff;
    acc.add(pv);
  }
  double value = acc.mean;
  double var = acc.variance();
  double se = (acc.count > 0) ? std::sqrt(std::max(0.0, var / static_cast<double>(acc.count))) : 0.0;
  return {value, se};
}

}

