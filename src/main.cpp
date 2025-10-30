#include <cctype>
#include <cstdlib>
#include <iomanip>
#include <iostream>
#include <string>
#include <vector>
#include <optional>
#include "quant/version.hpp"
#include "quant/black_scholes.hpp"
#include "quant/barrier.hpp"
#include "quant/bs_barrier.hpp"
#include "quant/mc.hpp"
#include "quant/math.hpp"
#include "quant/mc_barrier.hpp"
#include "quant/pde.hpp"
#include "quant/pde_barrier.hpp"
#include "quant/american.hpp"
#include "quant/digital.hpp"
#include "quant/asian.hpp"
#include "quant/lookback.hpp"
#include "quant/heston.hpp"
#include "quant/risk.hpp"

#ifdef QUANT_HAS_OPENMP
#include <omp.h>
#endif

namespace {

std::string to_lower(std::string s) {
    for (auto& ch : s) {
        ch = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
    }
    return s;
}

quant::OptionType parse_option(const std::string& token) {
    std::string v = to_lower(token);
    if (v == "call" || v == "c") return quant::OptionType::Call;
    if (v == "put" || v == "p") return quant::OptionType::Put;
    throw std::runtime_error("Unknown option type: " + token);
}

quant::OptionType parse_pde_option(const std::string& token) {
    return parse_option(token);
}

quant::mc::McParams::Qmc parse_qmc_sampler(const std::string& token) {
    std::string v = to_lower(token);
    if (v == "none" || v == "0" || v.empty()) return quant::mc::McParams::Qmc::None;
    if (v == "sobol" || v == "1") return quant::mc::McParams::Qmc::Sobol;
    if (v == "sobol_scrambled" || v == "scrambled" || v == "2") return quant::mc::McParams::Qmc::SobolScrambled;
    throw std::runtime_error("Unknown sampler: " + token);
}

quant::mc::McParams::Bridge parse_bridge_mode(const std::string& token) {
    std::string v = to_lower(token);
    if (v == "none" || v == "0" || v.empty()) return quant::mc::McParams::Bridge::None;
    if (v == "bb" || v == "brownian" || v == "bridge" || v == "brownianbridge" || v == "1")
        return quant::mc::McParams::Bridge::BrownianBridge;
    throw std::runtime_error("Unknown bridge mode: " + token);
}

quant::rng::Mode parse_rng_mode(const std::string& token) {
    std::string v = to_lower(token);
    if (v == "counter" || v == "cb") return quant::rng::Mode::Counter;
    if (v == "mt19937" || v == "mt" || v == "pcg") return quant::rng::Mode::Mt19937;
    throw std::runtime_error("Unknown rng mode: " + token);
}

void apply_thread_override(int threads) {
#ifdef QUANT_HAS_OPENMP
    if (threads > 0) {
        omp_set_num_threads(threads);
    }
#else
    (void)threads;
#endif
}

void print_mc_result(const quant::mc::McResult& res, bool json, bool show_ci) {
    if (json) {
        std::cout << "{\"price\":" << res.estimate.value
                  << ",\"std_error\":" << res.estimate.std_error
                  << ",\"ci_low\":" << res.estimate.ci_low
                  << ",\"ci_high\":" << res.estimate.ci_high
                  << "}\n";
    } else {
        std::cout << res.estimate.value;
        if (show_ci) {
            std::cout << " +/- " << res.estimate.std_error
                      << " (95% CI=[" << res.estimate.ci_low << ", " << res.estimate.ci_high << "])\n";
        } else {
            std::cout << " (se=" << res.estimate.std_error << ")\n";
        }
    }
}

void print_scalar(double value, bool json) {
    if (json) {
        std::cout << "{\"price\":" << value << "}\n";
    } else {
        std::cout << value << "\n";
    }
}

void print_psor(const quant::american::PsorResult& res, bool json) {
    if (json) {
        std::cout << "{\"price\":" << res.price
                  << ",\"iterations\":" << res.total_iterations
                  << ",\"max_residual\":" << res.max_residual
                  << "}\n";
    } else {
        std::cout << res.price << " (iterations=" << res.total_iterations
                  << ", residual=" << res.max_residual << ")\n";
    }
}

void print_lsmc(const quant::american::LsmcResult& res, bool json) {
    if (json) {
        std::cout << "{\"price\":" << res.price
                  << ",\"std_error\":" << res.std_error
                  << "}\n";
    } else {
        std::cout << res.price << " (se=" << res.std_error << ")\n";
    }
}

bool starts_with_dash(const char* arg) {
    return arg != nullptr && arg[0] == '-';
}

} // namespace

int main(int argc, char** argv) {
    if (argc <= 1) {
        std::cout << "quant-pricer-cpp " << quant::version_string() << "\n";
        std::cout << "Usage: quant_cli <engine> [params]\n";
        std::cout << "Engines: bs, iv, mc, barrier, pde, american, digital, asian, heston, risk\n";
        return 0;
    }
    std::string engine = argv[1];
    if (engine == "bs") {
        if (argc < 9) {
            std::cerr << "bs <S> <K> <r> <q> <sigma> <T> <call|put> [--json]\n";
            return 1;
        }
        double S = std::atof(argv[2]);
        double K = std::atof(argv[3]);
        double r = std::atof(argv[4]);
        double q = std::atof(argv[5]);
        double sig = std::atof(argv[6]);
        double T = std::atof(argv[7]);
        std::string type = argv[8];
        bool json = false;
        for (int idx = 9; idx < argc; ++idx) {
            std::string flag = argv[idx];
            if (flag == "--json") {
                json = true;
            } else {
                std::cerr << "Unknown flag " << flag << "\n";
                return 1;
            }
        }
        if (type == "call") {
            double price = quant::bs::call_price(S, K, r, q, sig, T);
            print_scalar(price, json);
        } else {
            double price = quant::bs::put_price(S, K, r, q, sig, T);
            print_scalar(price, json);
        }
        return 0;
    } else if (engine == "iv") {
        if (argc < 9) {
            std::cerr << "iv <call|put> <S> <K> <r> <q> <T> <price> [--json]\n";
            return 1;
        }
        std::string type = argv[2];
        double S = std::atof(argv[3]);
        double K = std::atof(argv[4]);
        double r = std::atof(argv[5]);
        double q = std::atof(argv[6]);
        double T = std::atof(argv[7]);
        double price = std::atof(argv[8]);
        bool json = false;
        for (int idx = 9; idx < argc; ++idx) { std::string flag = argv[idx]; if (flag == "--json") json = true; else { std::cerr << "Unknown flag " << flag << "\n"; return 1; } }
        double iv = (type == "call") ? quant::bs::implied_vol_call(S,K,r,q,T,price)
                                      : quant::bs::implied_vol_put(S,K,r,q,T,price);
        if (json) std::cout << "{\"iv\":" << iv << "}\n"; else std::cout << iv << "\n";
        return 0;
    } else if (engine == "mc") {
        if (argc < 12) {
            std::cerr << "mc <S> <K> <r> <q> <sigma> <T> <paths> <seed> <antithetic:0|1> <qmc_mode> [bridge_mode] [num_steps]"
                         " [--sampler=] [--bridge=] [--steps=] [--rng=counter|mt19937] [--threads=] [--greeks] [--ci] [--json]\n";
            return 1;
        }
        quant::mc::McParams p{};
        p.spot = std::atof(argv[2]);
        p.strike = std::atof(argv[3]);
        p.rate = std::atof(argv[4]);
        p.dividend = std::atof(argv[5]);
        p.vol = std::atof(argv[6]);
        p.time = std::atof(argv[7]);
        p.num_paths = static_cast<std::uint64_t>(std::atoll(argv[8]));
        p.seed = static_cast<std::uint64_t>(std::atoll(argv[9]));
        p.antithetic = std::atoi(argv[10]) != 0;
        p.control_variate = true;
        try {
            p.qmc = parse_qmc_sampler(argv[11]);
        } catch (const std::exception& ex) {
            std::cerr << ex.what() << "\n";
            return 1;
        }
        int next = 12;
        if (argc > next && !starts_with_dash(argv[next])) {
            try {
                p.bridge = parse_bridge_mode(argv[next]);
            } catch (const std::exception& ex) {
                std::cerr << ex.what() << "\n";
                return 1;
            }
            ++next;
        }
        if (argc > next && !starts_with_dash(argv[next])) {
            p.num_steps = std::max(1, std::atoi(argv[next]));
            ++next;
        }

        bool json = false;
        bool show_ci = false;
        bool compute_greeks = false;
        int thread_override = -1;

        for (int idx = next; idx < argc; ++idx) {
            std::string flag = argv[idx];
            if (flag == "--json") {
                json = true;
            } else if (flag == "--ci") {
                show_ci = true;
            } else if (flag == "--greeks") {
                compute_greeks = true;
            } else if (flag.rfind("--sampler=", 0) == 0) {
                std::string value = flag.substr(10);
                try {
                    p.qmc = parse_qmc_sampler(value);
                } catch (const std::exception& ex) {
                    std::cerr << ex.what() << "\n";
                    return 1;
                }
            } else if (flag.rfind("--bridge=", 0) == 0) {
                std::string value = flag.substr(9);
                try {
                    p.bridge = parse_bridge_mode(value);
                } catch (const std::exception& ex) {
                    std::cerr << ex.what() << "\n";
                    return 1;
                }
            } else if (flag.rfind("--steps=", 0) == 0) {
                p.num_steps = std::max(1, std::atoi(flag.substr(8).c_str()));
            } else if (flag.rfind("--rng=", 0) == 0) {
                std::string value = flag.substr(6);
                try {
                    p.rng = parse_rng_mode(value);
                } catch (const std::exception& ex) {
                    std::cerr << ex.what() << "\n";
                    return 1;
                }
            } else if (flag.rfind("--threads=", 0) == 0) {
                thread_override = std::max(1, std::atoi(flag.substr(10).c_str()));
            } else {
                std::cerr << "Unknown flag " << flag << "\n";
                return 1;
            }
        }

        apply_thread_override(thread_override);
        auto res = quant::mc::price_european_call(p);
        std::optional<quant::mc::GreeksResult> greeks;
        if (compute_greeks) {
            greeks = quant::mc::greeks_european_call(p);
        }
        if (json) {
            int threads_used = 1;
#ifdef QUANT_HAS_OPENMP
            threads_used = (thread_override > 0) ? thread_override : omp_get_max_threads();
#else
            (void)thread_override;
#endif
            std::cout << "{\"price\":" << res.estimate.value
                      << ",\"std_error\":" << res.estimate.std_error
                      << ",\"ci_low\":" << res.estimate.ci_low
                      << ",\"ci_high\":" << res.estimate.ci_high
                      << ",\"paths\":" << p.num_paths
                      << ",\"seed\":" << p.seed
                      << ",\"antithetic\":" << (p.antithetic ? 1 : 0)
                      << ",\"sampler\":\"" << (p.qmc == quant::mc::McParams::Qmc::None ? "prng" : (p.qmc == quant::mc::McParams::Qmc::Sobol ? "sobol" : "sobol_scrambled")) << "\""
                      << ",\"bridge\":\"" << (p.bridge == quant::mc::McParams::Bridge::None ? "none" : "bb") << "\""
                      << ",\"steps\":" << p.num_steps
                      << ",\"rng\":\"" << (p.rng == quant::rng::Mode::Counter ? "counter" : "mt19937") << "\""
                      << ",\"threads\":" << threads_used;
            if (greeks) {
                auto emit_stat = [&](const char* name, const quant::mc::McStatistic& stat) {
                    std::cout << "\"" << name << "\":{"
                              << "\"value\":" << stat.value
                              << ",\"std_error\":" << stat.std_error
                              << ",\"ci_low\":" << stat.ci_low
                              << ",\"ci_high\":" << stat.ci_high
                              << "}";
                };
                std::cout << ",\"greeks\":{";
                emit_stat("delta", greeks->delta);
                std::cout << ",";
                emit_stat("vega", greeks->vega);
                std::cout << ",";
                emit_stat("gamma_lrm", greeks->gamma_lrm);
                std::cout << ",";
                emit_stat("gamma_pathwise", greeks->gamma_mixed);
                std::cout << ",";
                emit_stat("theta", greeks->theta);
                std::cout << "}";
            }
            std::cout << "}\n";
        } else {
            print_mc_result(res, false, show_ci);
            if (greeks) {
                auto print_stat = [&](const std::string& label, const quant::mc::McStatistic& stat) {
                    std::cout << label << ": " << stat.value;
                    if (show_ci) {
                        std::cout << " +/- " << stat.std_error
                                  << " (95% CI=[" << stat.ci_low << ", " << stat.ci_high << "])";
                    } else {
                        std::cout << " (se=" << stat.std_error << ")";
                    }
                    std::cout << "\n";
                };
                std::cout << "Greeks (LR/pathwise):\n";
                print_stat("  Delta", greeks->delta);
                print_stat("  Vega", greeks->vega);
                print_stat("  Gamma (LR)", greeks->gamma_lrm);
                print_stat("  Gamma (pathwise)", greeks->gamma_mixed);
                print_stat("  Theta", greeks->theta);
            }
        }
        return 0;
    } else if (engine == "barrier") {
        if (argc < 4) {
            std::cerr << "barrier <bs|mc|pde> ...\n";
            return 1;
        }
        std::string method = argv[2];
        auto parse_barrier_dir = [&](const std::string& s) -> bool {
            std::string v = to_lower(s);
            if (v == "up") return true;
            if (v == "down") return false;
            throw std::runtime_error("Unknown barrier direction: " + s);
        };
        auto parse_barrier_style = [&](const std::string& s) -> bool {
            std::string v = to_lower(s);
            if (v == "out") return true;
            if (v == "in") return false;
            throw std::runtime_error("Unknown barrier style: " + s);
        };
        auto build_spec = [&](bool up, bool out, double B, double rebate) {
            quant::BarrierSpec spec{};
            if (up && out) spec.type = quant::BarrierType::UpOut;
            else if (up && !out) spec.type = quant::BarrierType::UpIn;
            else if (!up && out) spec.type = quant::BarrierType::DownOut;
            else spec.type = quant::BarrierType::DownIn;
            spec.B = B;
            spec.rebate = rebate;
            return spec;
        };

        if (method == "bs") {
            if (argc < 14) {
                std::cerr << "barrier bs <call|put> <up|down> <in|out> <S> <K> <B> <rebate> <r> <q> <sigma> <T>\n";
                return 1;
            }
            try {
                quant::OptionType opt = parse_option(argv[3]);
                bool up = parse_barrier_dir(argv[4]);
                bool out = parse_barrier_style(argv[5]);
                double S = std::atof(argv[6]);
                double K = std::atof(argv[7]);
                double B = std::atof(argv[8]);
                double rebate = std::atof(argv[9]);
                double r = std::atof(argv[10]);
                double q = std::atof(argv[11]);
                double sigma = std::atof(argv[12]);
                double T = std::atof(argv[13]);
                quant::BarrierSpec spec = build_spec(up, out, B, rebate);
                double value = quant::bs::reiner_rubinstein_price(opt, spec, S, K, r, q, sigma, T);
                std::cout << value << "\n";
            } catch (const std::exception& ex) {
                std::cerr << ex.what() << "\n";
                return 1;
            }
            return 0;
        }
        if (method == "mc") {
            if (argc < 20) {
                std::cerr << "barrier mc <call|put> <up|down> <in|out> <S> <K> <B> <rebate> <r> <q> <sigma> <T> <paths> <seed> <antithetic:0|1> <qmc_mode> <bridge_mode> <num_steps>\n";
                return 1;
            }
            try {
                quant::OptionType opt = parse_option(argv[3]);
                bool up = parse_barrier_dir(argv[4]);
                bool out = parse_barrier_style(argv[5]);
                double S = std::atof(argv[6]);
                double K = std::atof(argv[7]);
                double B = std::atof(argv[8]);
                double rebate = std::atof(argv[9]);
                double r = std::atof(argv[10]);
                double q = std::atof(argv[11]);
                double sigma = std::atof(argv[12]);
                double T = std::atof(argv[13]);
                std::uint64_t paths = static_cast<std::uint64_t>(std::atoll(argv[14]));
                std::uint64_t seed = static_cast<std::uint64_t>(std::atoll(argv[15]));
                bool antithetic = std::atoi(argv[16]) != 0;
                std::string qmc_mode = argv[17];
                std::string bridge_mode = argv[18];
                int num_steps = std::atoi(argv[19]);

                quant::BarrierSpec spec = build_spec(up, out, B, rebate);
                quant::mc::McParams p{};
                p.spot = S;
                p.strike = K;
                p.rate = r;
                p.dividend = q;
                p.vol = sigma;
                p.time = T;
                p.num_paths = paths;
                p.seed = seed;
                p.antithetic = antithetic;
                p.control_variate = false;
                p.qmc = parse_qmc_sampler(qmc_mode);
                p.bridge = parse_bridge_mode(bridge_mode);
                p.num_steps = std::max(1, num_steps);

                bool json = false;
                bool show_ci = false;
                int thread_override = -1;
                for (int idx = 20; idx < argc; ++idx) {
                    std::string flag = argv[idx];
                    if (flag == "--json") {
                        json = true;
                    } else if (flag == "--ci") {
                        show_ci = true;
                    } else if (flag == "--cv") {
                        p.control_variate = true;
                        std::cerr << "warning: barrier MC control variate is experimental and may introduce bias\n";
                    } else if (flag.rfind("--sampler=", 0) == 0) {
                        p.qmc = parse_qmc_sampler(flag.substr(10));
                    } else if (flag.rfind("--bridge=", 0) == 0) {
                        p.bridge = parse_bridge_mode(flag.substr(9));
                    } else if (flag.rfind("--steps=", 0) == 0) {
                        p.num_steps = std::max(1, std::atoi(flag.substr(8).c_str()));
                    } else if (flag.rfind("--rng=", 0) == 0) {
                        try {
                            p.rng = parse_rng_mode(flag.substr(6));
                        } catch (const std::exception& ex) {
                            std::cerr << ex.what() << "\n";
                            return 1;
                        }
                    } else if (flag.rfind("--threads=", 0) == 0) {
                        thread_override = std::max(1, std::atoi(flag.substr(10).c_str()));
                    } else {
                        std::cerr << "Unknown flag " << flag << "\n";
                        return 1;
                    }
                }
                apply_thread_override(thread_override);
                auto res = quant::mc::price_barrier_option(p, K, opt, spec);
                if (json) {
                    int threads_used = 1;
#ifdef QUANT_HAS_OPENMP
                    threads_used = (thread_override > 0) ? thread_override : omp_get_max_threads();
#else
                    (void)thread_override;
#endif
                    std::cout << "{\"price\":" << res.estimate.value
                              << ",\"std_error\":" << res.estimate.std_error
                              << ",\"ci_low\":" << res.estimate.ci_low
                              << ",\"ci_high\":" << res.estimate.ci_high
                              << ",\"paths\":" << p.num_paths
                              << ",\"seed\":" << p.seed
                              << ",\"antithetic\":" << (p.antithetic ? 1 : 0)
                              << ",\"sampler\":\"" << (p.qmc == quant::mc::McParams::Qmc::None ? "prng" : (p.qmc == quant::mc::McParams::Qmc::Sobol ? "sobol" : "sobol_scrambled")) << "\""
                              << ",\"bridge\":\"" << (p.bridge == quant::mc::McParams::Bridge::None ? "none" : "bb") << "\""
                              << ",\"steps\":" << p.num_steps
                              << ",\"rng\":\"" << (p.rng == quant::rng::Mode::Counter ? "counter" : "mt19937") << "\""
                              << ",\"threads\":" << threads_used
                              << "}\n";
                } else {
                    print_mc_result(res, false, show_ci);
                }
            } catch (const std::exception& ex) {
                std::cerr << ex.what() << "\n";
                return 1;
            }
            return 0;
        }
        if (method == "pde") {
            if (argc < 17) {
                std::cerr << "barrier pde <call|put> <up|down> <in|out> <S> <K> <B> <rebate> <r> <q> <sigma> <T> <space_nodes> <time_steps> <smax_mult> [--json]\n";
                return 1;
            }
            try {
                quant::OptionType opt = parse_option(argv[3]);
                bool up = parse_barrier_dir(argv[4]);
                bool out = parse_barrier_style(argv[5]);
                double S = std::atof(argv[6]);
                double K = std::atof(argv[7]);
                double B = std::atof(argv[8]);
                double rebate = std::atof(argv[9]);
                double r = std::atof(argv[10]);
                double q = std::atof(argv[11]);
                double sigma = std::atof(argv[12]);
                double T = std::atof(argv[13]);
                int space_nodes = std::max(3, std::atoi(argv[14]));
                int time_steps = std::max(1, std::atoi(argv[15]));
                double smax_mult = std::atof(argv[16]);

                quant::BarrierSpec spec = build_spec(up, out, B, rebate);
                quant::pde::BarrierPdeParams p{};
                p.spot = S;
                p.strike = K;
                p.rate = r;
                p.dividend = q;
                p.vol = sigma;
                p.time = T;
                p.barrier = spec;
                p.grid = quant::pde::GridSpec{space_nodes, time_steps, smax_mult};
                bool json = false;
                for (int idx = 17; idx < argc; ++idx) {
                    std::string flag = argv[idx];
                    if (flag == "--json") json = true; else { std::cerr << "Unknown flag " << flag << "\n"; return 1; }
                }
                if (json) {
                    auto gres = quant::pde::price_barrier_crank_nicolson_greeks(p, opt);
                    std::cout << "{\"price\":" << gres.price
                              << ",\"delta\":" << gres.delta
                              << ",\"gamma\":" << gres.gamma
                              << "}\n";
                } else {
                    double value = quant::pde::price_barrier_crank_nicolson(p, opt);
                    std::cout << value << "\n";
                }
            } catch (const std::exception& ex) {
                std::cerr << ex.what() << "\n";
                return 1;
            }
            return 0;
        }
        std::cerr << "Unknown barrier method: " << method << "\n";
        return 1;
    } else if (engine == "american") {
        if (argc < 3) {
            std::cerr << "american <binomial|psor|lsmc> ...\n";
            return 1;
        }
        std::string method = argv[2];
        if (method == "binomial") {
            if (argc < 11) {
                std::cerr << "american binomial <call|put> <S> <K> <r> <q> <sigma> <T> <steps> [--json]\n";
                return 1;
            }
            quant::OptionType opt;
            try {
                opt = parse_option(argv[3]);
            } catch (const std::exception& ex) {
                std::cerr << ex.what() << "\n";
                return 1;
            }
            quant::american::Params base{
                .spot = std::atof(argv[4]),
                .strike = std::atof(argv[5]),
                .rate = std::atof(argv[6]),
                .dividend = std::atof(argv[7]),
                .vol = std::atof(argv[8]),
                .time = std::atof(argv[9]),
                .type = opt
            };
            int steps = std::max(1, std::atoi(argv[10]));
            bool json = false;
            for (int idx = 11; idx < argc; ++idx) {
                std::string flag = argv[idx];
                if (flag == "--json") {
                    json = true;
                } else {
                    std::cerr << "Unknown flag " << flag << "\n";
                    return 1;
                }
            }
            double price = quant::american::price_binomial_crr(base, steps);
            print_scalar(price, json);
            return 0;
        }
        if (method == "psor") {
            if (argc < 15) {
                std::cerr << "american psor <call|put> <S> <K> <r> <q> <sigma> <T> <M> <N> <SmaxMult> [logspace:0|1] [neumann:0|1] [stretch] [omega] [max_iter] [tol] [--json]\n";
                return 1;
            }
            quant::OptionType opt;
            try {
                opt = parse_option(argv[3]);
            } catch (const std::exception& ex) {
                std::cerr << ex.what() << "\n";
                return 1;
            }
            quant::american::PsorParams params{
                .base = {
                    .spot = std::atof(argv[4]),
                    .strike = std::atof(argv[5]),
                    .rate = std::atof(argv[6]),
                    .dividend = std::atof(argv[7]),
                    .vol = std::atof(argv[8]),
                    .time = std::atof(argv[9]),
                    .type = opt
                },
                .grid = quant::pde::GridSpec{std::atoi(argv[10]), std::atoi(argv[11]), std::atof(argv[12])},
                .log_space = true,
                .upper_boundary = quant::pde::PdeParams::UpperBoundary::Neumann,
                .stretch = 2.0,
                .omega = 1.5,
                .max_iterations = 8000,
                .tolerance = 1e-8,
                .use_rannacher = true
            };
            int idx = 13;
            if (argc > idx) {
                params.log_space = std::atoi(argv[idx]) != 0;
                ++idx;
            }
            if (argc > idx) {
                params.upper_boundary = (std::atoi(argv[idx]) != 0)
                    ? quant::pde::PdeParams::UpperBoundary::Neumann
                    : quant::pde::PdeParams::UpperBoundary::Dirichlet;
                ++idx;
            }
            if (argc > idx) {
                params.stretch = std::max(0.0, std::atof(argv[idx]));
                ++idx;
            }
            if (argc > idx) {
                params.omega = std::atof(argv[idx]);
                ++idx;
            }
            if (argc > idx) {
                params.max_iterations = std::max(100, std::atoi(argv[idx]));
                ++idx;
            }
            if (argc > idx) {
                params.tolerance = std::atof(argv[idx]);
                ++idx;
            }
            bool json = false;
            for (int flag_idx = idx; flag_idx < argc; ++flag_idx) {
                std::string flag = argv[flag_idx];
                if (flag == "--json") json = true;
                else {
                    std::cerr << "Unknown flag " << flag << "\n";
                    return 1;
                }
            }
            auto res = quant::american::price_psor(params);
            print_psor(res, json);
            return 0;
        }
        if (method == "lsmc") {
            if (argc < 12) {
                std::cerr << "american lsmc <call|put> <S> <K> <r> <q> <sigma> <T> <paths> <steps> <seed> [antithetic:0|1] [--json]\n";
                return 1;
            }
            quant::OptionType opt;
            try {
                opt = parse_option(argv[3]);
            } catch (const std::exception& ex) {
                std::cerr << ex.what() << "\n";
                return 1;
            }
            quant::american::LsmcParams params{
                .base = {
                    .spot = std::atof(argv[4]),
                    .strike = std::atof(argv[5]),
                    .rate = std::atof(argv[6]),
                    .dividend = std::atof(argv[7]),
                    .vol = std::atof(argv[8]),
                    .time = std::atof(argv[9]),
                    .type = opt
                },
                .num_paths = static_cast<std::uint64_t>(std::atoll(argv[10])),
                .seed = static_cast<std::uint64_t>(std::atoll(argv[12])),
                .num_steps = std::max(1, std::atoi(argv[11])),
                .antithetic = false
            };
            int idx = 13;
            if (argc > idx && !starts_with_dash(argv[idx])) {
                params.antithetic = std::atoi(argv[idx]) != 0;
                ++idx;
            }
            bool json = false;
            for (int flag_idx = idx; flag_idx < argc; ++flag_idx) {
                std::string flag = argv[flag_idx];
                if (flag == "--json") json = true;
                else {
                    std::cerr << "Unknown flag " << flag << "\n";
                    return 1;
                }
            }
            auto res = quant::american::price_lsmc(params);
            print_lsmc(res, json);
            return 0;
        }
        std::cerr << "Unknown american method: " << method << "\n";
        return 1;
    } else if (engine == "pde") {
        if (argc < 12) {
            std::cerr << "pde <S> <K> <r> <q> <sigma> <T> <call|put> <M> <N> <SmaxMult> [logspace:0|1] [neumann:0|1] [stretch] [theta:0|1] [rannacher:0|1] [--json]\n";
            return 1;
        }
        quant::pde::PdeParams pp{};
        pp.spot = std::atof(argv[2]);
        pp.strike = std::atof(argv[3]);
        pp.rate = std::atof(argv[4]);
        pp.dividend = std::atof(argv[5]);
        pp.vol = std::atof(argv[6]);
        pp.time = std::atof(argv[7]);
        std::string type = argv[8];
        pp.type = (type == "call") ? quant::OptionType::Call : quant::OptionType::Put;
        int M = std::atoi(argv[9]);
        int N = std::atoi(argv[10]);
        double smax = std::atof(argv[11]);
        pp.grid = quant::pde::GridSpec{M, N, smax};
        int idx = 12;
        if (argc > idx && !starts_with_dash(argv[idx])) {
            pp.log_space = std::atoi(argv[idx]) != 0;
            ++idx;
        }
        if (argc > idx && !starts_with_dash(argv[idx])) {
            pp.upper_boundary = (std::atoi(argv[idx]) != 0)
                ? quant::pde::PdeParams::UpperBoundary::Neumann
                : quant::pde::PdeParams::UpperBoundary::Dirichlet;
            ++idx;
        }
        if (argc > idx && !starts_with_dash(argv[idx])) {
            pp.grid.stretch = std::max(0.0, std::atof(argv[idx]));
            ++idx;
        }
        if (argc > idx && !starts_with_dash(argv[idx])) {
            pp.compute_theta = std::atoi(argv[idx]) != 0;
            ++idx;
        } else {
            pp.compute_theta = true;
        }
        if (argc > idx && !starts_with_dash(argv[idx])) {
            pp.use_rannacher = std::atoi(argv[idx]) != 0;
            ++idx;
        }

        bool json = false;
        for (int flag_idx = idx; flag_idx < argc; ++flag_idx) {
            std::string flag = argv[flag_idx];
            if (flag == "--json") json = true;
            else {
                std::cerr << "Unknown flag " << flag << "\n";
                return 1;
            }
        }

        quant::pde::PdeResult res = quant::pde::price_crank_nicolson(pp);
        if (json) {
            std::cout << "{\"price\":" << res.price
                      << ",\"delta\":" << res.delta
                      << ",\"gamma\":" << res.gamma;
            if (res.theta.has_value()) {
                std::cout << ",\"theta\":" << *res.theta;
            } else {
                std::cout << ",\"theta\":null";
            }
            std::cout << "}\n";
        } else {
            std::cout << res.price << " (delta=" << res.delta << ", gamma=" << res.gamma;
            if (res.theta.has_value()) {
                std::cout << ", theta=" << *res.theta;
            }
            std::cout << ")\n";
        }
        return 0;
    } else if (engine == "digital") {
        if (argc < 10) {
            std::cerr << "digital <cash|asset> <call|put> <S> <K> <r> <q> <sigma> <T> [--json]\n";
            return 1;
        }
        std::string kind = argv[2];
        std::string type = argv[3];
        quant::digital::Params p{
            .spot = std::atof(argv[4]),
            .strike = std::atof(argv[5]),
            .rate = std::atof(argv[6]),
            .dividend = std::atof(argv[7]),
            .vol = std::atof(argv[8]),
            .time = std::atof(argv[9]),
            .call = (type == "call")
        };
        bool json = false;
        for (int idx = 10; idx < argc; ++idx) {
            std::string flag = argv[idx];
            if (flag == "--json") json = true; else { std::cerr << "Unknown flag " << flag << "\n"; return 1; }
        }
        quant::digital::Type t = (kind == "cash") ? quant::digital::Type::CashOrNothing : quant::digital::Type::AssetOrNothing;
        double price = quant::digital::price_bs(p, t);
        print_scalar(price, json);
        return 0;
    } else if (engine == "asian") {
        if (argc < 15) {
            std::cerr << "asian <arith|geom> <fixed|float> <S> <K> <r> <q> <sigma> <T> <paths> <steps> <seed> [--no_cv] [--json]\n";
            return 1;
        }
        std::string avg = argv[2];
        std::string pay = argv[3];
        quant::asian::McParams p{
            .spot = std::atof(argv[4]),
            .strike = std::atof(argv[5]),
            .rate = std::atof(argv[6]),
            .dividend = std::atof(argv[7]),
            .vol = std::atof(argv[8]),
            .time = std::atof(argv[9]),
            .num_paths = static_cast<std::uint64_t>(std::atoll(argv[10])),
            .seed = static_cast<std::uint64_t>(std::atoll(argv[12])),
            .num_steps = std::max(1, std::atoi(argv[11])),
            .antithetic = true,
            .use_geometric_cv = true,
            .payoff = (pay == "fixed") ? quant::asian::Payoff::FixedStrike : quant::asian::Payoff::FloatingStrike,
            .avg = (avg == "arith") ? quant::asian::Average::Arithmetic : quant::asian::Average::Geometric
        };
        bool json = false;
        for (int idx = 13; idx < argc; ++idx) {
            std::string flag = argv[idx];
            if (flag == "--no_cv") p.use_geometric_cv = false;
            else if (flag == "--json") json = true;
            else { std::cerr << "Unknown flag " << flag << "\n"; return 1; }
        }
        auto res = quant::asian::price_mc(p);
        if (json) {
            std::cout << "{\"price\":" << res.value << ",\"std_error\":" << res.std_error
                      << ",\"ci_low\":" << res.ci_low << ",\"ci_high\":" << res.ci_high << "}\n";
        } else {
            std::cout << res.value << " (se=" << res.std_error << ", 95% CI=[" << res.ci_low << ", " << res.ci_high << "])\n";
        }
        return 0;
    } else if (engine == "lookback") {
        if (argc < 14) {
            std::cerr << "lookback <fixed|float> <call|put> <S> <K> <r> <q> <sigma> <T> <paths> <steps> <seed> [--no_anti] [--json]\n";
            return 1;
        }
        std::string kind = argv[2];
        quant::OptionType opt = parse_option(argv[3]);
        quant::lookback::McParams p{
            .spot = std::atof(argv[4]),
            .strike = std::atof(argv[5]),
            .rate = std::atof(argv[6]),
            .dividend = std::atof(argv[7]),
            .vol = std::atof(argv[8]),
            .time = std::atof(argv[9]),
            .num_paths = static_cast<std::uint64_t>(std::atoll(argv[10])),
            .seed = static_cast<std::uint64_t>(std::atoll(argv[12])),
            .num_steps = std::max(1, std::atoi(argv[11])),
            .antithetic = true,
            .use_bridge = true,
            .opt = opt,
            .type = (kind == "fixed") ? quant::lookback::Type::FixedStrike : quant::lookback::Type::FloatingStrike
        };
        bool json = false;
        for (int idx = 13; idx < argc; ++idx) {
            std::string flag = argv[idx];
            if (flag == "--no_anti") p.antithetic = false;
            else if (flag == "--json") json = true;
            else { std::cerr << "Unknown flag " << flag << "\n"; return 1; }
        }
        auto res = quant::lookback::price_mc(p);
        if (json) {
            std::cout << "{\"price\":" << res.value << ",\"std_error\":" << res.std_error
                      << ",\"ci_low\":" << res.ci_low << ",\"ci_high\":" << res.ci_high << "}\n";
        } else {
            std::cout << res.value << " (se=" << res.std_error << ", 95% CI=[" << res.ci_low << ", " << res.ci_high << "])\n";
        }
        return 0;
    } else if (engine == "heston") {
        if (argc < 15) {
            std::cerr << "heston <kappa> <theta> <sigma_v> <rho> <v0> <S> <K> <r> <q> <T> <paths> <steps> <seed> [--mc] [--json]\n";
            return 1;
        }
        quant::heston::Params h{std::atof(argv[2]), std::atof(argv[3]), std::atof(argv[4]), std::atof(argv[5]), std::atof(argv[6])};
        quant::heston::MarketParams mkt{std::atof(argv[7]), std::atof(argv[8]), std::atof(argv[9]), std::atof(argv[10]), std::atof(argv[11])};
        std::uint64_t paths = static_cast<std::uint64_t>(std::atoll(argv[12]));
        int steps = std::max(1, std::atoi(argv[13]));
        std::uint64_t seed = static_cast<std::uint64_t>(std::atoll(argv[14]));
        quant::heston::McParams mc_params{mkt, h, paths, seed, steps, true};
        mc_params.scheme = quant::heston::McParams::Scheme::QE;
        mc_params.rng = quant::rng::Mode::Counter;
        bool show_ci = false;
        bool use_mc = false;
        bool json = false;
        for (int idx = 15; idx < argc; ++idx) {
            std::string flag = argv[idx];
            if (flag == "--mc") {
                use_mc = true;
            } else if (flag == "--json") {
                json = true;
            } else if (flag == "--ci") {
                show_ci = true;
            } else if (flag == "--no-anti") {
                mc_params.antithetic = false;
            } else if (flag == "--heston-qe") {
                mc_params.scheme = quant::heston::McParams::Scheme::QE;
            } else if (flag == "--heston-euler") {
                mc_params.scheme = quant::heston::McParams::Scheme::Euler;
            } else if (flag.rfind("--rng=", 0) == 0) {
                std::string value = flag.substr(6);
                try {
                    mc_params.rng = parse_rng_mode(value);
                } catch (const std::exception& ex) {
                    std::cerr << ex.what() << "\n";
                    return 1;
                }
            } else {
                std::cerr << "Unknown flag " << flag << "\n";
                return 1;
            }
        }
        const double analytic = quant::heston::call_analytic(mkt, h);
        if (!use_mc) {
            print_scalar(analytic, json);
            return 0;
        }
        auto res = quant::heston::call_qe_mc(mc_params);
        const double err = std::abs(res.price - analytic);
        const double tolerance = std::max(1e-3, 5.0 * res.std_error);
        if (err > tolerance) {
            std::cerr << "warning: Heston MC deviates from analytic price by "
                      << err << " (tolerance=" << tolerance << "); treat MC output as diagnostic only.\n";
        }
        const double half_width = quant::math::kZ95 * res.std_error;
        const double ci_low = res.price - half_width;
        const double ci_high = res.price + half_width;
        if (json) {
            std::cout << "{\"price\":" << res.price
                      << ",\"std_error\":" << res.std_error
                      << ",\"ci_low\":" << ci_low
                      << ",\"ci_high\":" << ci_high
                      << ",\"analytic\":" << analytic
                      << ",\"abs_error\":" << err
                      << ",\"rng\":\"" << (mc_params.rng == quant::rng::Mode::Counter ? "counter" : "mt19937") << "\""
                      << ",\"scheme\":\"" << (mc_params.scheme == quant::heston::McParams::Scheme::QE ? "qe" : "euler") << "\""
                      << "}\n";
        } else {
            std::cout << res.price;
            if (show_ci) {
                std::cout << " +/- " << res.std_error
                          << " (95% CI=[" << ci_low << ", " << ci_high << "])";
            } else {
                std::cout << " (se=" << res.std_error << ")";
            }
            std::cout << " (analytic=" << analytic
                      << ", |err|=" << err
                      << ", rng=" << (mc_params.rng == quant::rng::Mode::Counter ? "counter" : "mt19937")
                      << ", scheme=" << (mc_params.scheme == quant::heston::McParams::Scheme::QE ? "QE" : "Euler")
                      << ")\n";
        }
        return 0;
    } else if (engine == "risk") {
        if (argc < 10) {
            std::cerr << "risk gbm <S> <mu> <sigma> <T_years> <position> <sims> <seed> <alpha> [--json]\n";
            return 1;
        }
        std::string method = argv[2];
        if (method != "gbm") { std::cerr << "Unknown risk method\n"; return 1; }
        double S = std::atof(argv[3]);
        double mu = std::atof(argv[4]);
        double sig = std::atof(argv[5]);
        double T = std::atof(argv[6]);
        double pos = std::atof(argv[7]);
        unsigned long sims = static_cast<unsigned long>(std::atol(argv[8]));
        unsigned long seed = static_cast<unsigned long>(std::atol(argv[9]));
        double alpha = std::atof(argv[10]);
        bool json = false;
        for (int idx = 11; idx < argc; ++idx) { std::string flag = argv[idx]; if (flag == "--json") json = true; else { std::cerr << "Unknown flag " << flag << "\n"; return 1; } }
        auto res = quant::risk::var_cvar_gbm(S, mu, sig, T, pos, sims, seed, alpha);
        if (json) std::cout << "{\"var\":" << res.var << ",\"cvar\":" << res.cvar << "}\n";
        else std::cout << "VaR=" << res.var << ", CVaR=" << res.cvar << "\n";
        return 0;
    }
    std::cerr << "Unknown engine: " << engine << "\n";
    return 1;
}
