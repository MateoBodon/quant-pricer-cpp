#include <pybind11/complex.h>
#include <pybind11/numpy.h>
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "quant/american.hpp"
#include "quant/black_scholes.hpp"
#include "quant/bs_barrier.hpp"
#include "quant/heston.hpp"
#include "quant/mc.hpp"
#include "quant/mc_barrier.hpp"
#include "quant/multi.hpp"
#include "quant/pde.hpp"
#include "quant/pde_barrier.hpp"
#include "quant/portfolio.hpp"
#include "quant/risk.hpp"
#include "quant/version.hpp"
#include <algorithm>
#include <cmath>
#include <limits>
#include <semaphore>
#include <stdexcept>
#include <thread>
#include <vector>

namespace py = pybind11;

namespace {

constexpr std::size_t kHestonBatchMaxWorkers = 4;
constexpr std::size_t kHestonBatchItemsPerWorker = 32;
std::counting_semaphore<static_cast<std::ptrdiff_t>(kHestonBatchMaxWorkers)> heston_batch_worker_slots{
    static_cast<std::ptrdiff_t>(kHestonBatchMaxWorkers)};

class HestonBatchWorkerLease {
  public:
    explicit HestonBatchWorkerLease(std::size_t desired_workers) {
        heston_batch_worker_slots.acquire();
        acquired_workers_ = 1;
        while (acquired_workers_ < desired_workers && heston_batch_worker_slots.try_acquire()) {
            ++acquired_workers_;
        }
    }

    ~HestonBatchWorkerLease() {
        heston_batch_worker_slots.release(static_cast<std::ptrdiff_t>(acquired_workers_));
    }

    HestonBatchWorkerLease(const HestonBatchWorkerLease&) = delete;
    HestonBatchWorkerLease& operator=(const HestonBatchWorkerLease&) = delete;

    [[nodiscard]] std::size_t worker_count() const { return acquired_workers_; }

  private:
    std::size_t acquired_workers_{0};
};

enum class HestonBatchOutput { Call, Put, ImpliedVol, CallMetrics };

void validate_heston_values(const py::array_t<double, py::array::c_style | py::array::forcecast>& markets,
                            const py::array_t<double, py::array::c_style | py::array::forcecast>& params) {
    const double* market_data = markets.data();
    for (py::ssize_t index = 0; index < markets.shape(0); ++index) {
        const double* row = market_data + index * 5;
        const bool finite = std::all_of(row, row + 5, [](double value) { return std::isfinite(value); });
        const bool valid = row[0] > 0.0 && row[1] > 0.0 && row[4] > 0.0;
        if (!finite || !valid) {
            throw std::invalid_argument("batch contains nonfinite or invalid Heston inputs");
        }
    }
    const double* param_data = params.data();
    for (py::ssize_t index = 0; index < params.shape(0); ++index) {
        const double* row = param_data + index * 5;
        const bool finite = std::all_of(row, row + 5, [](double value) { return std::isfinite(value); });
        const bool valid =
            row[0] > 0.0 && row[1] > 0.0 && row[2] > 0.0 && row[3] > -1.0 && row[3] < 1.0 && row[4] > 0.0;
        if (!finite || !valid) {
            throw std::invalid_argument("batch contains nonfinite or invalid Heston inputs");
        }
    }
}

py::array_t<double>
heston_analytic_batch(const py::array_t<double, py::array::c_style | py::array::forcecast>& markets,
                      const py::array_t<double, py::array::c_style | py::array::forcecast>& params,
                      HestonBatchOutput output) {
    if (markets.ndim() != 2 || markets.shape(1) != 5) {
        throw std::invalid_argument("markets must have shape (n, 5): spot, strike, rate, dividend, time");
    }
    if (params.ndim() != 2 || params.shape(1) != 5) {
        throw std::invalid_argument("params must have shape (n, 5): kappa, theta, sigma, rho, v0");
    }
    const py::ssize_t market_count = markets.shape(0);
    const py::ssize_t parameter_count = params.shape(0);
    if (market_count == 0 || parameter_count == 0) {
        throw std::invalid_argument("markets and params must be non-empty");
    }
    if (market_count != parameter_count && market_count != 1 && parameter_count != 1) {
        throw std::invalid_argument("markets and params must have one row or matching row counts");
    }
    validate_heston_values(markets, params);
    const py::ssize_t output_count = std::max(market_count, parameter_count);
    const bool broadcast_markets = market_count == 1;
    const bool broadcast_params = parameter_count == 1;
    const bool call_metrics = output == HestonBatchOutput::CallMetrics;
    py::array_t<double> results =
        call_metrics ? py::array_t<double>(py::array::ShapeContainer{output_count, py::ssize_t{2}})
                     : py::array_t<double>(py::array::ShapeContainer{output_count});
    const double* market_data = markets.data();
    const double* param_data = params.data();
    double* result_data = results.mutable_data();
    const std::size_t item_count = static_cast<std::size_t>(output_count);
    const std::size_t desired_workers = std::min(
        kHestonBatchMaxWorkers,
        std::max<std::size_t>(1, (item_count + kHestonBatchItemsPerWorker - 1) / kHestonBatchItemsPerWorker));
    {
        py::gil_scoped_release release;
        HestonBatchWorkerLease worker_lease(desired_workers);
        const std::size_t worker_count = worker_lease.worker_count();
        const std::size_t chunk_size = (item_count + worker_count - 1) / worker_count;
        auto price_range = [=](std::size_t begin, std::size_t end) {
            for (std::size_t index = begin; index < end; ++index) {
                const double* market_row = market_data + (broadcast_markets ? 0 : index * 5);
                const double* param_row = param_data + (broadcast_params ? 0 : index * 5);
                const quant::heston::MarketParams market{market_row[0], market_row[1], market_row[2],
                                                         market_row[3], market_row[4]};
                const quant::heston::Params parameter{param_row[0], param_row[1], param_row[2], param_row[3],
                                                      param_row[4]};
                switch (output) {
                case HestonBatchOutput::Call:
                    result_data[index] = quant::heston::call_analytic(market, parameter);
                    break;
                case HestonBatchOutput::Put:
                    result_data[index] = quant::heston::put_analytic(market, parameter);
                    break;
                case HestonBatchOutput::ImpliedVol:
                    result_data[index] = quant::heston::implied_vol_call(market, parameter);
                    break;
                case HestonBatchOutput::CallMetrics: {
                    const double call_price = quant::heston::call_analytic(market, parameter);
                    result_data[2 * index] = call_price;
                    result_data[2 * index + 1] = quant::bs::implied_vol_call(
                        market.spot, market.strike, market.rate, market.dividend, market.time, call_price);
                    break;
                }
                }
            }
        };
        if (worker_count == 1) {
            price_range(0, item_count);
        } else {
            std::vector<std::jthread> workers;
            workers.reserve(worker_count);
            for (std::size_t worker = 0; worker < worker_count; ++worker) {
                const std::size_t begin = worker * chunk_size;
                const std::size_t end = std::min(item_count, begin + chunk_size);
                if (begin >= end) {
                    break;
                }
                workers.emplace_back(price_range, begin, end);
            }
        }
    }
    return results;
}

py::array_t<double>
heston_call_metrics_grid(const py::array_t<double, py::array::c_style | py::array::forcecast>& markets,
                         const py::array_t<double, py::array::c_style | py::array::forcecast>& params) {
    if (markets.ndim() != 2 || markets.shape(1) != 5) {
        throw std::invalid_argument("markets must have shape (m, 5): spot, strike, rate, dividend, time");
    }
    if (params.ndim() != 2 || params.shape(1) != 5) {
        throw std::invalid_argument("params must have shape (p, 5): kappa, theta, sigma, rho, v0");
    }
    const py::ssize_t market_count = markets.shape(0);
    const py::ssize_t parameter_count = params.shape(0);
    if (market_count == 0 || parameter_count == 0) {
        throw std::invalid_argument("markets and params must be non-empty");
    }
    validate_heston_values(markets, params);
    const py::ssize_t max_items = std::numeric_limits<py::ssize_t>::max() / 2;
    if (parameter_count > max_items / market_count) {
        throw std::overflow_error("Heston call-metrics Cartesian grid is too large");
    }
    const py::ssize_t grid_item_count = parameter_count * market_count;
    py::array_t<double> results(py::array::ShapeContainer{parameter_count, market_count, py::ssize_t{2}});
    const double* market_data = markets.data();
    const double* param_data = params.data();
    double* result_data = results.mutable_data();
    const std::size_t item_count = static_cast<std::size_t>(grid_item_count);
    const std::size_t markets_per_parameter = static_cast<std::size_t>(market_count);
    const std::size_t desired_workers = std::min(
        kHestonBatchMaxWorkers,
        std::max<std::size_t>(1, (item_count + kHestonBatchItemsPerWorker - 1) / kHestonBatchItemsPerWorker));
    {
        py::gil_scoped_release release;
        HestonBatchWorkerLease worker_lease(desired_workers);
        const std::size_t worker_count = worker_lease.worker_count();
        const std::size_t chunk_size = (item_count + worker_count - 1) / worker_count;
        auto price_range = [=](std::size_t begin, std::size_t end) {
            for (std::size_t index = begin; index < end; ++index) {
                const std::size_t parameter_index = index / markets_per_parameter;
                const std::size_t market_index = index % markets_per_parameter;
                const double* market_row = market_data + market_index * 5;
                const double* param_row = param_data + parameter_index * 5;
                const quant::heston::MarketParams market{market_row[0], market_row[1], market_row[2],
                                                         market_row[3], market_row[4]};
                const quant::heston::Params parameter{param_row[0], param_row[1], param_row[2], param_row[3],
                                                      param_row[4]};
                const double call_price = quant::heston::call_analytic(market, parameter);
                result_data[2 * index] = call_price;
                result_data[2 * index + 1] = quant::bs::implied_vol_call(
                    market.spot, market.strike, market.rate, market.dividend, market.time, call_price);
            }
        };
        if (worker_count == 1) {
            price_range(0, item_count);
        } else {
            std::vector<std::jthread> workers;
            workers.reserve(worker_count);
            for (std::size_t worker = 0; worker < worker_count; ++worker) {
                const std::size_t begin = worker * chunk_size;
                const std::size_t end = std::min(item_count, begin + chunk_size);
                if (begin >= end) {
                    break;
                }
                workers.emplace_back(price_range, begin, end);
            }
        }
    }
    return results;
}

std::vector<quant::portfolio::VanillaPosition>
parse_portfolio_positions(const py::array_t<double, py::array::c_style | py::array::forcecast>& positions) {
    if (positions.ndim() != 2 || positions.shape(1) != 8) {
        throw std::invalid_argument("positions must have shape (n, 8): option_type, quantity, spot, strike, "
                                    "rate, dividend, volatility, time");
    }
    if (positions.shape(0) == 0) {
        throw std::invalid_argument("positions must be non-empty");
    }
    std::vector<quant::portfolio::VanillaPosition> parsed;
    parsed.reserve(static_cast<std::size_t>(positions.shape(0)));
    const double* data = positions.data();
    for (py::ssize_t index = 0; index < positions.shape(0); ++index) {
        const double* row = data + index * 8;
        quant::portfolio::OptionType type;
        if (row[0] == 1.0) {
            type = quant::portfolio::OptionType::Call;
        } else if (row[0] == -1.0) {
            type = quant::portfolio::OptionType::Put;
        } else {
            throw std::invalid_argument("portfolio option_type must be exactly 1 (call) or -1 (put)");
        }
        parsed.push_back({type, row[1], row[2], row[3], row[4], row[5], row[6], row[7]});
    }
    return parsed;
}

std::vector<quant::portfolio::MarketShock>
parse_portfolio_shocks(const py::array_t<double, py::array::c_style | py::array::forcecast>& shocks) {
    if (shocks.ndim() != 2 || shocks.shape(1) != 5) {
        throw std::invalid_argument("shocks must have shape (m, 5): spot_return, volatility_shift, "
                                    "rate_shift, dividend_shift, time_elapsed");
    }
    if (shocks.shape(0) == 0) {
        throw std::invalid_argument("shocks must be non-empty");
    }
    std::vector<quant::portfolio::MarketShock> parsed;
    parsed.reserve(static_cast<std::size_t>(shocks.shape(0)));
    const double* data = shocks.data();
    for (py::ssize_t index = 0; index < shocks.shape(0); ++index) {
        const double* row = data + index * 5;
        parsed.push_back({row[0], row[1], row[2], row[3], row[4]});
    }
    return parsed;
}

py::dict
portfolio_risk_batch(const py::array_t<double, py::array::c_style | py::array::forcecast>& positions) {
    const auto parsed = parse_portfolio_positions(positions);
    quant::portfolio::RiskResult result;
    {
        py::gil_scoped_release release;
        result = quant::portfolio::price_risk(parsed);
    }
    py::array_t<double> position_metrics(
        py::array::ShapeContainer{static_cast<py::ssize_t>(result.positions.size()), py::ssize_t{7}});
    double* position_data = position_metrics.mutable_data();
    for (std::size_t index = 0; index < result.positions.size(); ++index) {
        const auto& risk = result.positions[index];
        const double row[7]{risk.price, risk.value, risk.delta, risk.gamma, risk.vega, risk.theta, risk.rho};
        std::copy(row, row + 7, position_data + 7 * index);
    }
    py::array_t<double> totals(py::array::ShapeContainer{py::ssize_t{6}});
    const double values[6]{result.totals.value, result.totals.delta, result.totals.gamma,
                           result.totals.vega,  result.totals.theta, result.totals.rho};
    std::copy(values, values + 6, totals.mutable_data());
    py::dict output;
    output["position_metrics"] = std::move(position_metrics);
    output["portfolio_totals"] = std::move(totals);
    output["position_columns"] = py::make_tuple("price", "value", "delta", "gamma", "vega", "theta", "rho");
    output["total_columns"] = py::make_tuple("value", "delta", "gamma", "vega", "theta", "rho");
    return output;
}

py::dict
portfolio_scenario_pnl(const py::array_t<double, py::array::c_style | py::array::forcecast>& positions,
                       const py::array_t<double, py::array::c_style | py::array::forcecast>& shocks,
                       bool detail) {
    const auto parsed_positions = parse_portfolio_positions(positions);
    const auto parsed_shocks = parse_portfolio_shocks(shocks);
    quant::portfolio::ScenarioResult result;
    {
        py::gil_scoped_release release;
        result = quant::portfolio::scenario_pnl(parsed_positions, parsed_shocks, detail);
    }
    py::array_t<double> portfolio_pnl(
        py::array::ShapeContainer{static_cast<py::ssize_t>(result.scenario_count)});
    std::copy(result.portfolio_pnl.begin(), result.portfolio_pnl.end(), portfolio_pnl.mutable_data());
    py::dict output;
    output["base_portfolio_value"] = result.base_portfolio_value;
    output["portfolio_pnl"] = std::move(portfolio_pnl);
    if (detail) {
        py::array_t<double> position_pnl(
            py::array::ShapeContainer{static_cast<py::ssize_t>(result.scenario_count),
                                      static_cast<py::ssize_t>(result.position_count)});
        std::copy(result.position_pnl.begin(), result.position_pnl.end(), position_pnl.mutable_data());
        output["position_pnl"] = std::move(position_pnl);
    } else {
        output["position_pnl"] = py::none();
    }
    return output;
}

} // namespace

PYBIND11_MODULE(pyquant_pricer, m) {
    m.doc() = "Python bindings for quant-pricer-cpp (BS/MC/PDE subset)";
    m.attr("__version__") = quant::version_string();

    // Black–Scholes
    m.def("bs_call", (double (*)(double, double, double, double, double, double))&quant::bs::call_price,
          "Black-Scholes call price", py::arg("S"), py::arg("K"), py::arg("r"), py::arg("q"),
          py::arg("sigma"), py::arg("T"));
    m.def("bs_put", (double (*)(double, double, double, double, double, double))&quant::bs::put_price,
          "Black-Scholes put price", py::arg("S"), py::arg("K"), py::arg("r"), py::arg("q"), py::arg("sigma"),
          py::arg("T"));
    m.def("bs_delta_call", &quant::bs::delta_call, "BS call delta", py::arg("S"), py::arg("K"), py::arg("r"),
          py::arg("q"), py::arg("sigma"), py::arg("T"));
    m.def("bs_gamma", &quant::bs::gamma, "BS gamma", py::arg("S"), py::arg("K"), py::arg("r"), py::arg("q"),
          py::arg("sigma"), py::arg("T"));
    m.def("bs_vega", &quant::bs::vega, "BS vega", py::arg("S"), py::arg("K"), py::arg("r"), py::arg("q"),
          py::arg("sigma"), py::arg("T"));
    m.def("bs_iv_call", &quant::bs::implied_vol_call, "BS implied vol from call", py::arg("S"), py::arg("K"),
          py::arg("r"), py::arg("q"), py::arg("T"), py::arg("price"));

    // Monte Carlo: price and Greeks
    m.def("mc_european_call", &quant::mc::price_european_call, "MC price (European call)", py::arg("params"));
    m.def("mc_greeks_call", &quant::mc::greeks_european_call, "MC Greeks (European call)", py::arg("params"));

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

    py::class_<quant::mc::McResult>(m, "McResult").def_readonly("estimate", &quant::mc::McResult::estimate);

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
        .def_property_readonly("theta", [](const quant::pde::PdeResult& r) {
            return r.theta.has_value() ? py::cast(*r.theta) : py::none();
        });

    m.def("pde_price", &quant::pde::price_crank_nicolson, "PDE price (Crank–Nicolson)", py::arg("params"));

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

    m.def("barrier_bs", &quant::bs::reiner_rubinstein_price, py::arg("opt"), py::arg("barrier"), py::arg("S"),
          py::arg("K"), py::arg("r"), py::arg("q"), py::arg("sigma"), py::arg("T"));

    m.def("barrier_mc", &quant::mc::price_barrier_option, py::arg("params"), py::arg("K"), py::arg("opt"),
          py::arg("barrier"));

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
    m.def("heston_put_analytic", &quant::heston::put_analytic, py::arg("mkt"), py::arg("params"));
    m.def(
        "heston_calls_analytic_batch",
        [](const py::array_t<double, py::array::c_style | py::array::forcecast>& markets,
           const py::array_t<double, py::array::c_style | py::array::forcecast>& params) {
            return heston_analytic_batch(markets, params, HestonBatchOutput::Call);
        },
        py::arg("markets"), py::arg("params"),
        "Price contiguous (n,5) market and parameter matrices with the native analytic engine.");
    m.def(
        "heston_puts_analytic_batch",
        [](const py::array_t<double, py::array::c_style | py::array::forcecast>& markets,
           const py::array_t<double, py::array::c_style | py::array::forcecast>& params) {
            return heston_analytic_batch(markets, params, HestonBatchOutput::Put);
        },
        py::arg("markets"), py::arg("params"),
        "Price European puts for contiguous (n,5) matrices using analytic calls and put-call parity.");
    m.def(
        "heston_implied_vols_batch",
        [](const py::array_t<double, py::array::c_style | py::array::forcecast>& markets,
           const py::array_t<double, py::array::c_style | py::array::forcecast>& params) {
            return heston_analytic_batch(markets, params, HestonBatchOutput::ImpliedVol);
        },
        py::arg("markets"), py::arg("params"),
        "Compute Black-Scholes implied vols from analytic Heston calls for contiguous (n,5) matrices.");
    m.def(
        "heston_call_metrics_batch",
        [](const py::array_t<double, py::array::c_style | py::array::forcecast>& markets,
           const py::array_t<double, py::array::c_style | py::array::forcecast>& params) {
            return heston_analytic_batch(markets, params, HestonBatchOutput::CallMetrics);
        },
        py::arg("markets"), py::arg("params"),
        "Return contiguous (n,2) analytic Heston call_price and implied_vol columns with one integration per "
        "row.");
    m.def("heston_call_metrics_grid", &heston_call_metrics_grid, py::arg("markets"), py::arg("params"),
          "Return a contiguous candidate-major (p,m,2) call_price and implied_vol Cartesian grid.");
    m.def(
        "heston_analytic_batch_policy",
        []() {
            py::dict policy;
            policy["max_process_workers"] = kHestonBatchMaxWorkers;
            policy["items_per_worker"] = kHestonBatchItemsPerWorker;
            return policy;
        },
        "Return the fixed process-wide worker budget for analytic Heston batches.");
    m.def("heston_characteristic_fn", &quant::heston::characteristic_function, py::arg("u"), py::arg("mkt"),
          py::arg("params"), "Risk-neutral characteristic function φ(u)");
    m.def("heston_implied_vol", &quant::heston::implied_vol_call, py::arg("mkt"), py::arg("params"),
          "Black–Scholes implied vol implied by Heston analytic price");

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
          py::arg("horizon_years"), py::arg("position"), py::arg("num_sims"), py::arg("seed"),
          py::arg("alpha"));
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
    m.def("kupiec_christoffersen", &quant::risk::kupiec_christoffersen, py::arg("exceptions"),
          py::arg("alpha"));
    m.def("var_cvar_t", &quant::risk::var_cvar_t, py::arg("mu"), py::arg("sigma"), py::arg("nu"),
          py::arg("horizon_years"), py::arg("position"), py::arg("num_sims"), py::arg("seed"),
          py::arg("alpha"));

    // Vectorized vanilla portfolio valuation and exact-repricing scenarios.
    m.def("bs_portfolio_risk", &portfolio_risk_batch, py::arg("positions"),
          "Return position metrics and quantity-weighted portfolio Black-Scholes risk totals for an (n,8) "
          "matrix.");
    m.def("bs_portfolio_scenarios", &portfolio_scenario_pnl, py::arg("positions"), py::arg("shocks"),
          py::arg("detail") = false,
          "Exact-reprice an (n,8) vanilla portfolio under an (m,5) shock matrix; detail=False avoids the m*n "
          "output.");

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
