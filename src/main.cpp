#include <cctype>
#include <cstdlib>
#include <iostream>
#include <string>
#include "quant/version.hpp"
#include "quant/black_scholes.hpp"
#include "quant/mc.hpp"
#include "quant/pde.hpp"

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
    } else if (engine == "pde") {
        if (argc < 12) {
            std::cerr << "pde <S> <K> <r> <q> <sigma> <T> <call|put> <M> <N> <SmaxMult> [logspace:0|1] [neumann:0|1]\n";
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
        double price = quant::pde::price_crank_nicolson(pp);
        std::cout << price << "\n";
        return 0;
    }
    std::cerr << "Unknown engine: " << engine << "\n";
    return 1;
}
