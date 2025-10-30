#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
// Optional: add numpy later for zero-copy arrays
//#include <pybind11/numpy.h>

#include "quant/black_scholes.hpp"
#include "quant/mc.hpp"
#include "quant/pde.hpp"
#include "quant/american.hpp"
#include "quant/bs_barrier.hpp"
#include "quant/mc_barrier.hpp"
#include "quant/pde_barrier.hpp"
#include "quant/heston.hpp"
#include "quant/risk.hpp"
#include "quant/multi.hpp"

namespace py = pybind11;

PYBIND11_MODULE(pyquant_pricer, m) {
    m.doc() = "Python bindings for quant-pricer-cpp (BS/MC/PDE subset)";

    // Black–Scholes
    m.def("bs_call", (double (*)(double,double,double,double,double,double)) &quant::bs::call_price, "Black-Scholes call price",
          py::arg("S"), py::arg("K"), py::arg("r"), py::arg("q"), py::arg("sigma"), py::arg("T"));
    m.def("bs_put", (double (*)(double,double,double,double,double,double)) &quant::bs::put_price, "Black-Scholes put price",
          py::arg("S"), py::arg("K"), py::arg("r"), py::arg("q"), py::arg("sigma"), py::arg("T"));
    m.def("bs_delta_call", &quant::bs::delta_call, "BS call delta",
          py::arg("S"), py::arg("K"), py::arg("r"), py::arg("q"), py::arg("sigma"), py::arg("T"));
    m.def("bs_gamma", &quant::bs::gamma, "BS gamma",
          py::arg("S"), py::arg("K"), py::arg("r"), py::arg("q"), py::arg("sigma"), py::arg("T"));
    m.def("bs_vega", &quant::bs::vega, "BS vega",
          py::arg("S"), py::arg("K"), py::arg("r"), py::arg("q"), py::arg("sigma"), py::arg("T"));
    m.def("bs_iv_call", &quant::bs::implied_vol_call, "BS implied vol from call",
          py::arg("S"), py::arg("K"), py::arg("r"), py::arg("q"), py::arg("T"), py::arg("price"));

    // Monte Carlo: price and Greeks
    m.def("mc_european_call", &quant::mc::price_european_call, "MC price (European call)",
          py::arg("params"));
    m.def("mc_greeks_call", &quant::mc::greeks_european_call, "MC Greeks (European call)",
          py::arg("params"));

    py::class_<quant::PiecewiseConstant>(m, "PiecewiseConstant")
        .def(py::init<>())
        .def_readwrite("times", &quant::PiecewiseConstant::times)
        .def_readwrite("values", &quant::PiecewiseConstant::values)
        .def("value", &quant::PiecewiseConstant::value);

    py::enum_<quant::mc::McParams::Qmc>(m, "McSampler")
        .value("None", quant::mc::McParams::Qmc::None)
        .value("Sobol", quant::mc::McParams::Qmc::Sobol)
        .value("SobolScrambled", quant::mc::McParams::Qmc::SobolScrambled);

    py::enum_<quant::mc::McParams::Bridge>(m, "McBridge")
        .value("None", quant::mc::McParams::Bridge::None)
        .value("BrownianBridge", quant::mc::McParams::Bridge::BrownianBridge);

    py::enum_<quant::rng::Mode>(m, "McRng")
        .value("Mt19937", quant::rng::Mode::Mt19937)
        .value("Counter", quant::rng::Mode::Counter);

    py::class_<quant::mc::McParams>(m, "McParams")
        .def(py::init<>())
        .def_readwrite("spot", &quant::mc::McParams::spot)
        .def_readwrite("strike", &quant::mc::McParams::strike)
        .def_readwrite("rate", &quant::mc::McParams::rate)
        .def_readwrite("dividend", &quant::mc::McParams::dividend)
        .def_readwrite("vol", &quant::mc::McParams::vol)
        .def_readwrite("time", &quant::mc::McParams::time)
        .def_readwrite("num_paths", &quant::mc::McParams::num_paths)
        .def_readwrite("seed", &quant::mc::McParams::seed)
        .def_readwrite("antithetic", &quant::mc::McParams::antithetic)
        .def_readwrite("control_variate", &quant::mc::McParams::control_variate)
        .def_readwrite("rng", &quant::mc::McParams::rng)
        .def_readwrite("qmc", &quant::mc::McParams::qmc)
        .def_readwrite("bridge", &quant::mc::McParams::bridge)
        .def_readwrite("num_steps", &quant::mc::McParams::num_steps)
        .def_readwrite("rate_schedule", &quant::mc::McParams::rate_schedule)
        .def_readwrite("dividend_schedule", &quant::mc::McParams::dividend_schedule)
        .def_readwrite("vol_schedule", &quant::mc::McParams::vol_schedule);

    py::class_<quant::mc::McStatistic>(m, "McStatistic")
        .def_readonly("value", &quant::mc::McStatistic::value)
        .def_readonly("std_error", &quant::mc::McStatistic::std_error)
        .def_readonly("ci_low", &quant::mc::McStatistic::ci_low)
        .def_readonly("ci_high", &quant::mc::McStatistic::ci_high);

    py::class_<quant::mc::McResult>(m, "McResult")
        .def_readonly("estimate", &quant::mc::McResult::estimate);

    py::class_<quant::mc::GreeksResult>(m, "McGreeks")
        .def_readonly("delta", &quant::mc::GreeksResult::delta)
        .def_readonly("vega", &quant::mc::GreeksResult::vega)
        .def_readonly("gamma_lrm", &quant::mc::GreeksResult::gamma_lrm)
        .def_readonly("gamma_mixed", &quant::mc::GreeksResult::gamma_mixed)
        .def_readonly("theta", &quant::mc::GreeksResult::theta);

    // PDE pricing (Δ/Γ/Θ)
    py::class_<quant::pde::GridSpec>(m, "GridSpec")
        .def(py::init<>())
        .def_readwrite("num_space", &quant::pde::GridSpec::num_space)
        .def_readwrite("num_time", &quant::pde::GridSpec::num_time)
        .def_readwrite("s_max_mult", &quant::pde::GridSpec::s_max_mult)
        .def_readwrite("stretch", &quant::pde::GridSpec::stretch);

    py::class_<quant::pde::PdeParams>(m, "PdeParams")
        .def(py::init<>())
        .def_readwrite("spot", &quant::pde::PdeParams::spot)
        .def_readwrite("strike", &quant::pde::PdeParams::strike)
        .def_readwrite("rate", &quant::pde::PdeParams::rate)
        .def_readwrite("dividend", &quant::pde::PdeParams::dividend)
        .def_readwrite("vol", &quant::pde::PdeParams::vol)
        .def_readwrite("time", &quant::pde::PdeParams::time)
        .def_readwrite("type", &quant::pde::PdeParams::type)
        .def_readwrite("grid", &quant::pde::PdeParams::grid)
        .def_readwrite("log_space", &quant::pde::PdeParams::log_space)
        .def_readwrite("compute_theta", &quant::pde::PdeParams::compute_theta)
        .def_readwrite("use_rannacher", &quant::pde::PdeParams::use_rannacher);

    py::class_<quant::pde::PdeResult>(m, "PdeResult")
        .def_readonly("price", &quant::pde::PdeResult::price)
        .def_readonly("delta", &quant::pde::PdeResult::delta)
        .def_readonly("gamma", &quant::pde::PdeResult::gamma)
        .def_property_readonly("theta", [](const quant::pde::PdeResult& r){ return r.theta.has_value() ? py::cast(*r.theta) : py::none(); });

    m.def("pde_price", &quant::pde::price_crank_nicolson, "PDE price (Crank–Nicolson)",
          py::arg("params"));

    // American
    py::enum_<quant::OptionType>(m, "OptionType")
        .value("Call", quant::OptionType::Call)
        .value("Put", quant::OptionType::Put);

    py::enum_<quant::BarrierType>(m, "BarrierType")
        .value("UpOut", quant::BarrierType::UpOut)
        .value("DownOut", quant::BarrierType::DownOut)
        .value("UpIn", quant::BarrierType::UpIn)
        .value("DownIn", quant::BarrierType::DownIn);

    py::class_<quant::american::Params>(m, "AmParams")
        .def(py::init<>())
        .def_readwrite("spot", &quant::american::Params::spot)
        .def_readwrite("strike", &quant::american::Params::strike)
        .def_readwrite("rate", &quant::american::Params::rate)
        .def_readwrite("dividend", &quant::american::Params::dividend)
        .def_readwrite("vol", &quant::american::Params::vol)
        .def_readwrite("time", &quant::american::Params::time)
        .def_readwrite("type", &quant::american::Params::type);

    m.def("american_binomial", &quant::american::price_binomial_crr, py::arg("params"), py::arg("steps"));

    py::class_<quant::american::PsorParams>(m, "PsorParams")
        .def(py::init<>())
        .def_readwrite("base", &quant::american::PsorParams::base)
        .def_readwrite("grid", &quant::american::PsorParams::grid)
        .def_readwrite("log_space", &quant::american::PsorParams::log_space)
        .def_readwrite("omega", &quant::american::PsorParams::omega)
        .def_readwrite("max_iterations", &quant::american::PsorParams::max_iterations)
        .def_readwrite("tolerance", &quant::american::PsorParams::tolerance)
        .def_readwrite("use_rannacher", &quant::american::PsorParams::use_rannacher);

    py::class_<quant::american::PsorResult>(m, "PsorResult")
        .def_readonly("price", &quant::american::PsorResult::price)
        .def_readonly("total_iterations", &quant::american::PsorResult::total_iterations)
        .def_readonly("max_residual", &quant::american::PsorResult::max_residual);

    m.def("american_psor", &quant::american::price_psor, py::arg("params"));

    py::class_<quant::american::LsmcParams>(m, "LsmcParams")
        .def(py::init<>())
        .def_readwrite("base", &quant::american::LsmcParams::base)
        .def_readwrite("num_paths", &quant::american::LsmcParams::num_paths)
        .def_readwrite("seed", &quant::american::LsmcParams::seed)
        .def_readwrite("num_steps", &quant::american::LsmcParams::num_steps)
        .def_readwrite("antithetic", &quant::american::LsmcParams::antithetic);

    py::class_<quant::american::LsmcResult>(m, "LsmcResult")
        .def_readonly("price", &quant::american::LsmcResult::price)
        .def_readonly("std_error", &quant::american::LsmcResult::std_error);

    m.def("american_lsmc", &quant::american::price_lsmc, py::arg("params"));

    // Barriers
    py::class_<quant::BarrierSpec>(m, "BarrierSpec")
        .def(py::init<>())
        .def_readwrite("type", &quant::BarrierSpec::type)
        .def_readwrite("B", &quant::BarrierSpec::B)
        .def_readwrite("rebate", &quant::BarrierSpec::rebate);

    m.def("barrier_bs", &quant::bs::reiner_rubinstein_price, py::arg("opt"), py::arg("barrier"),
          py::arg("S"), py::arg("K"), py::arg("r"), py::arg("q"), py::arg("sigma"), py::arg("T"));

    m.def("barrier_mc", &quant::mc::price_barrier_option, py::arg("params"), py::arg("K"), py::arg("opt"), py::arg("barrier"));

    m.def("barrier_pde_price", &quant::pde::price_barrier_crank_nicolson, py::arg("params"), py::arg("opt"));

    // Heston
    py::class_<quant::heston::Params>(m, "HestonParams")
        .def(py::init<>())
        .def_readwrite("kappa", &quant::heston::Params::kappa)
        .def_readwrite("theta", &quant::heston::Params::theta)
        .def_readwrite("sigma", &quant::heston::Params::sigma)
        .def_readwrite("rho", &quant::heston::Params::rho)
        .def_readwrite("v0", &quant::heston::Params::v0);

    py::class_<quant::heston::MarketParams>(m, "HestonMarket")
        .def(py::init<>())
        .def_readwrite("spot", &quant::heston::MarketParams::spot)
        .def_readwrite("strike", &quant::heston::MarketParams::strike)
        .def_readwrite("rate", &quant::heston::MarketParams::rate)
        .def_readwrite("dividend", &quant::heston::MarketParams::dividend)
        .def_readwrite("time", &quant::heston::MarketParams::time);

    m.def("heston_call_analytic", &quant::heston::call_analytic, py::arg("mkt"), py::arg("params"));

    py::enum_<quant::heston::McParams::Scheme>(m, "HestonScheme")
        .value("Euler", quant::heston::McParams::Scheme::Euler)
        .value("QE", quant::heston::McParams::Scheme::QE);

    py::class_<quant::heston::McParams>(m, "HestonMcParams")
        .def(py::init<>())
        .def_readwrite("mkt", &quant::heston::McParams::mkt)
        .def_readwrite("h", &quant::heston::McParams::h)
        .def_readwrite("num_paths", &quant::heston::McParams::num_paths)
        .def_readwrite("seed", &quant::heston::McParams::seed)
        .def_readwrite("num_steps", &quant::heston::McParams::num_steps)
        .def_readwrite("antithetic", &quant::heston::McParams::antithetic)
        .def_readwrite("rng", &quant::heston::McParams::rng)
        .def_readwrite("scheme", &quant::heston::McParams::scheme);

    py::class_<quant::heston::McResult>(m, "HestonMcResult")
        .def_readonly("price", &quant::heston::McResult::price)
        .def_readonly("std_error", &quant::heston::McResult::std_error);

    m.def("heston_call_qe_mc", &quant::heston::call_qe_mc, py::arg("params"));

    // Risk
    py::class_<quant::risk::VarEs>(m, "VarEs")
        .def_readonly("var", &quant::risk::VarEs::var)
        .def_readonly("cvar", &quant::risk::VarEs::cvar);

    m.def("var_cvar_from_pnl", &quant::risk::var_cvar_from_pnl, py::arg("pnl"), py::arg("alpha"));
    m.def("var_cvar_gbm", &quant::risk::var_cvar_gbm, py::arg("spot"), py::arg("mu"), py::arg("sigma"),
          py::arg("horizon_years"), py::arg("position"), py::arg("num_sims"), py::arg("seed"), py::arg("alpha"));
    py::class_<quant::risk::BacktestStats>(m, "BacktestStats")
        .def_readonly("alpha", &quant::risk::BacktestStats::alpha)
        .def_readonly("T", &quant::risk::BacktestStats::T)
        .def_readonly("N", &quant::risk::BacktestStats::N)
        .def_readonly("lr_pof", &quant::risk::BacktestStats::lr_pof)
        .def_readonly("p_pof", &quant::risk::BacktestStats::p_pof)
        .def_readonly("lr_ind", &quant::risk::BacktestStats::lr_ind)
        .def_readonly("p_ind", &quant::risk::BacktestStats::p_ind)
        .def_readonly("lr_cc", &quant::risk::BacktestStats::lr_cc)
        .def_readonly("p_cc", &quant::risk::BacktestStats::p_cc);
    m.def("kupiec_christoffersen", &quant::risk::kupiec_christoffersen, py::arg("exceptions"), py::arg("alpha"));
    m.def("var_cvar_t", &quant::risk::var_cvar_t, py::arg("mu"), py::arg("sigma"), py::arg("nu"),
          py::arg("horizon_years"), py::arg("position"), py::arg("num_sims"), py::arg("seed"), py::arg("alpha"));

    // Multi-asset & jumps
    py::class_<quant::multi::BasketMcParams>(m, "BasketMcParams")
        .def(py::init<>())
        .def_readwrite("spots", &quant::multi::BasketMcParams::spots)
        .def_readwrite("vols", &quant::multi::BasketMcParams::vols)
        .def_readwrite("dividends", &quant::multi::BasketMcParams::dividends)
        .def_readwrite("weights", &quant::multi::BasketMcParams::weights)
        .def_readwrite("corr", &quant::multi::BasketMcParams::corr)
        .def_readwrite("rate", &quant::multi::BasketMcParams::rate)
        .def_readwrite("strike", &quant::multi::BasketMcParams::strike)
        .def_readwrite("time", &quant::multi::BasketMcParams::time)
        .def_readwrite("num_paths", &quant::multi::BasketMcParams::num_paths)
        .def_readwrite("seed", &quant::multi::BasketMcParams::seed)
        .def_readwrite("antithetic", &quant::multi::BasketMcParams::antithetic);

    py::class_<quant::multi::McStat>(m, "McStat")
        .def_readonly("value", &quant::multi::McStat::value)
        .def_readonly("std_error", &quant::multi::McStat::std_error);

    m.def("basket_call_mc", &quant::multi::basket_european_call_mc, py::arg("params"));

    py::class_<quant::multi::MertonParams>(m, "MertonParams")
        .def(py::init<>())
        .def_readwrite("spot", &quant::multi::MertonParams::spot)
        .def_readwrite("strike", &quant::multi::MertonParams::strike)
        .def_readwrite("rate", &quant::multi::MertonParams::rate)
        .def_readwrite("dividend", &quant::multi::MertonParams::dividend)
        .def_readwrite("vol", &quant::multi::MertonParams::vol)
        .def_readwrite("time", &quant::multi::MertonParams::time)
        .def_readwrite("lambda_", &quant::multi::MertonParams::lambda)
        .def_readwrite("muJ", &quant::multi::MertonParams::muJ)
        .def_readwrite("sigmaJ", &quant::multi::MertonParams::sigmaJ)
        .def_readwrite("num_paths", &quant::multi::MertonParams::num_paths)
        .def_readwrite("seed", &quant::multi::MertonParams::seed)
        .def_readwrite("antithetic", &quant::multi::MertonParams::antithetic);

    m.def("merton_call_mc", &quant::multi::merton_call_mc, py::arg("params"));
}
