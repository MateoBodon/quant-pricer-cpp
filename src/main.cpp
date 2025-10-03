#include <cctype>
#include <cstdlib>
#include <iostream>
#include <string>
#include "quant/version.hpp"
#include "quant/black_scholes.hpp"
#include "quant/barrier.hpp"
#include "quant/bs_barrier.hpp"
#include "quant/mc.hpp"
#include "quant/mc_barrier.hpp"
#include "quant/pde.hpp"
#include "quant/pde_barrier.hpp"

int main(int argc, char** argv) {
    if (argc <= 1) {
        std::cout << "quant-pricer-cpp " << quant::version_string() << "\n";
        std::cout << "Usage: quant_cli <engine> [params]\n";
        std::cout << "Engines: bs, mc, pde\n";
        return 0;
    }
    std::string engine = argv[1];
    if (engine == "bs") {
        if (argc < 9) {
            std::cerr << "bs <S> <K> <r> <q> <sigma> <T> <call|put>\n";
            return 1;
        }
        double S = std::atof(argv[2]);
        double K = std::atof(argv[3]);
        double r = std::atof(argv[4]);
        double q = std::atof(argv[5]);
        double sig = std::atof(argv[6]);
        double T = std::atof(argv[7]);
        std::string type = argv[8];
        if (type == "call") {
            std::cout << quant::bs::call_price(S, K, r, q, sig, T) << "\n";
        } else {
            std::cout << quant::bs::put_price(S, K, r, q, sig, T) << "\n";
        }
        return 0;
    } else if (engine == "mc") {
        if (argc < 12) {
            std::cerr << "mc <S> <K> <r> <q> <sigma> <T> <paths> <seed> <antithetic:0|1> <qmc_mode> [bridge_mode] [num_steps]\n";
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
        auto to_lower = [](std::string s) {
            for (auto& ch : s) ch = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
            return s;
        };
        auto parse_qmc = [&](const std::string& token) {
            const std::string v = to_lower(token);
            if (v == "0" || v == "none") return quant::mc::McParams::Qmc::None;
            if (v == "1" || v == "sobol") return quant::mc::McParams::Qmc::Sobol;
            if (v == "2" || v == "sobol_scrambled" || v == "scrambled") return quant::mc::McParams::Qmc::SobolScrambled;
            throw std::runtime_error("Unknown QMC mode: " + token);
        };
        auto parse_bridge = [&](const std::string& token) {
            const std::string v = to_lower(token);
            if (v.empty() || v == "none" || v == "0") return quant::mc::McParams::Bridge::None;
            if (v == "bb" || v == "brownian" || v == "bridge" || v == "brownianbridge" || v == "1")
                return quant::mc::McParams::Bridge::BrownianBridge;
            throw std::runtime_error("Unknown bridge mode: " + token);
        };
        try {
            p.qmc = parse_qmc(argv[11]);
        } catch (const std::exception& ex) {
            std::cerr << ex.what() << "\n";
            return 1;
        }
        if (argc > 12) {
            try {
                p.bridge = parse_bridge(argv[12]);
            } catch (const std::exception& ex) {
                std::cerr << ex.what() << "\n";
                return 1;
            }
        }
        if (argc > 13) {
            p.num_steps = std::max(1, std::atoi(argv[13]));
        }
        auto res = quant::mc::price_european_call(p);
        std::cout << res.price << " (se=" << res.std_error << ")\n";
        return 0;
    } else if (engine == "barrier") {
        if (argc < 4) {
            std::cerr << "barrier <bs|mc|pde> ...\n";
            return 1;
        }
        std::string method = argv[2];
        auto to_lower = [](std::string s) {
            for (auto& ch : s) ch = static_cast<char>(std::tolower(static_cast<unsigned char>(ch)));
            return s;
        };
        auto parse_option = [&](const std::string& s) -> quant::OptionType {
            std::string v = to_lower(s);
            if (v == "call" || v == "c") return quant::OptionType::Call;
            if (v == "put" || v == "p") return quant::OptionType::Put;
            throw std::runtime_error("Unknown option type: " + s);
        };
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
                p.control_variate = true;
                auto lower = to_lower(qmc_mode);
                if (lower == "none" || lower == "0") p.qmc = quant::mc::McParams::Qmc::None;
                else if (lower == "sobol" || lower == "1") p.qmc = quant::mc::McParams::Qmc::Sobol;
                else if (lower == "sobol_scrambled" || lower == "scrambled" || lower == "2") p.qmc = quant::mc::McParams::Qmc::SobolScrambled;
                else throw std::runtime_error("Unknown qmc mode: " + qmc_mode);
                auto bridge_lower = to_lower(bridge_mode);
                if (bridge_lower == "none" || bridge_lower == "0") p.bridge = quant::mc::McParams::Bridge::None;
                else if (bridge_lower == "bb" || bridge_lower == "brownian" || bridge_lower == "1") p.bridge = quant::mc::McParams::Bridge::BrownianBridge;
                else throw std::runtime_error("Unknown bridge mode: " + bridge_mode);
                p.num_steps = std::max(1, num_steps);
                auto res = quant::mc::price_barrier_option(p, K, opt, spec);
                std::cout << res.price << " (se=" << res.std_error << ")\n";
            } catch (const std::exception& ex) {
                std::cerr << ex.what() << "\n";
                return 1;
            }
            return 0;
        }
        if (method == "pde") {
            if (argc < 17) {
                std::cerr << "barrier pde <call|put> <up|down> <in|out> <S> <K> <B> <rebate> <r> <q> <sigma> <T> <space_nodes> <time_steps> <smax_mult>\n";
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
                double value = quant::pde::price_barrier_crank_nicolson(p, opt);
                std::cout << value << "\n";
            } catch (const std::exception& ex) {
                std::cerr << ex.what() << "\n";
                return 1;
            }
            return 0;
        }
        std::cerr << "Unknown barrier method: " << method << "\n";
        return 1;
    } else if (engine == "pde") {
        if (argc < 12) {
            std::cerr << "pde <S> <K> <r> <q> <sigma> <T> <call|put> <M> <N> <SmaxMult> [logspace:0|1] [neumann:0|1] [stretch] [theta:0|1]\n";
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
        pp.type = (type == "call") ? quant::pde::OptionType::Call : quant::pde::OptionType::Put;
        int M = std::atoi(argv[9]);
        int N = std::atoi(argv[10]);
        double smax = std::atof(argv[11]);
        pp.grid = quant::pde::GridSpec{M, N, smax};
        if (argc > 12) {
            pp.log_space = std::atoi(argv[12]) != 0;
        }
        if (argc > 13) {
            pp.upper_boundary = (std::atoi(argv[13]) != 0) ? quant::pde::PdeParams::UpperBoundary::Neumann
                                                          : quant::pde::PdeParams::UpperBoundary::Dirichlet;
        }
        if (argc > 14) {
            pp.grid.stretch = std::max(0.0, std::atof(argv[14]));
        }
        if (argc > 15) {
            pp.compute_theta = std::atoi(argv[15]) != 0;
        } else {
            pp.compute_theta = true;
        }

        quant::pde::PdeResult res = quant::pde::price_crank_nicolson(pp);
        std::cout << res.price << " (delta=" << res.delta << ", gamma=" << res.gamma;
        if (res.theta.has_value()) {
            std::cout << ", theta=" << *res.theta;
        }
        std::cout << ")\n";
        return 0;
    }
    std::cerr << "Unknown engine: " << engine << "\n";
    return 1;
}
