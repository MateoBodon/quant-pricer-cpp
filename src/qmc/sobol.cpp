#include "quant/qmc/sobol.hpp"

#include <algorithm>
#include <array>
#include <cmath>
#include <limits>
#include <random>
#include <stdexcept>

namespace quant::qmc {

namespace {

struct SobolDirection {
    std::size_t dimension;
    unsigned s;
    unsigned a;
    std::array<unsigned, 9> m;
};

// Direction numbers from Joe & Kuo (2008), new-joe-kuo-6.21201 (first 64 dims).
static constexpr SobolDirection kSobolData[] = {
    { 1, 1, 0x0, {1, 0, 0, 0, 0, 0, 0, 0, 0} },
    { 2, 1, 0x0, {1, 0, 0, 0, 0, 0, 0, 0, 0} },
    { 3, 2, 0x1, {1, 3, 0, 0, 0, 0, 0, 0, 0} },
    { 4, 3, 0x1, {1, 3, 1, 0, 0, 0, 0, 0, 0} },
    { 5, 3, 0x2, {1, 1, 1, 0, 0, 0, 0, 0, 0} },
    { 6, 4, 0x1, {1, 1, 3, 3, 0, 0, 0, 0, 0} },
    { 7, 4, 0x4, {1, 3, 5, 13, 0, 0, 0, 0, 0} },
    { 8, 5, 0x2, {1, 1, 5, 5, 17, 0, 0, 0, 0} },
    { 9, 5, 0x4, {1, 1, 5, 5, 5, 0, 0, 0, 0} },
    { 10, 5, 0x7, {1, 1, 7, 11, 19, 0, 0, 0, 0} },
    { 11, 5, 0xB, {1, 1, 5, 1, 1, 0, 0, 0, 0} },
    { 12, 5, 0xD, {1, 1, 1, 3, 11, 0, 0, 0, 0} },
    { 13, 5, 0xE, {1, 3, 5, 5, 31, 0, 0, 0, 0} },
    { 14, 6, 0x1, {1, 3, 3, 9, 7, 49, 0, 0, 0} },
    { 15, 6, 0xD, {1, 1, 1, 15, 21, 21, 0, 0, 0} },
    { 16, 6, 0x10, {1, 3, 1, 13, 27, 49, 0, 0, 0} },
    { 17, 6, 0x13, {1, 1, 1, 15, 7, 5, 0, 0, 0} },
    { 18, 6, 0x16, {1, 3, 1, 15, 13, 25, 0, 0, 0} },
    { 19, 6, 0x19, {1, 1, 5, 5, 19, 61, 0, 0, 0} },
    { 20, 7, 0x1, {1, 3, 7, 11, 23, 15, 103, 0, 0} },
    { 21, 7, 0x4, {1, 3, 7, 13, 13, 15, 69, 0, 0} },
    { 22, 7, 0x7, {1, 1, 3, 13, 7, 35, 63, 0, 0} },
    { 23, 7, 0x8, {1, 3, 5, 9, 1, 25, 53, 0, 0} },
    { 24, 7, 0xE, {1, 3, 1, 13, 9, 35, 107, 0, 0} },
    { 25, 7, 0x13, {1, 3, 1, 5, 27, 61, 31, 0, 0} },
    { 26, 7, 0x15, {1, 1, 5, 11, 19, 41, 61, 0, 0} },
    { 27, 7, 0x1C, {1, 3, 5, 3, 3, 13, 69, 0, 0} },
    { 28, 7, 0x1F, {1, 1, 7, 13, 1, 19, 1, 0, 0} },
    { 29, 7, 0x20, {1, 3, 7, 5, 13, 19, 59, 0, 0} },
    { 30, 7, 0x25, {1, 1, 3, 9, 25, 29, 41, 0, 0} },
    { 31, 7, 0x29, {1, 3, 5, 13, 23, 1, 55, 0, 0} },
    { 32, 7, 0x2A, {1, 3, 7, 3, 13, 59, 17, 0, 0} },
    { 33, 7, 0x32, {1, 3, 1, 3, 5, 53, 69, 0, 0} },
    { 34, 7, 0x37, {1, 1, 5, 5, 23, 33, 13, 0, 0} },
    { 35, 7, 0x38, {1, 1, 7, 7, 1, 61, 123, 0, 0} },
    { 36, 7, 0x3B, {1, 1, 7, 9, 13, 61, 49, 0, 0} },
    { 37, 7, 0x3E, {1, 3, 3, 5, 3, 55, 33, 0, 0} },
    { 38, 8, 0xE, {1, 3, 1, 15, 31, 13, 49, 245, 0} },
    { 39, 8, 0x15, {1, 3, 5, 15, 31, 59, 63, 97, 0} },
    { 40, 8, 0x16, {1, 3, 1, 11, 11, 11, 77, 249, 0} },
    { 41, 8, 0x26, {1, 3, 1, 11, 27, 43, 71, 9, 0} },
    { 42, 8, 0x2F, {1, 1, 7, 15, 21, 11, 81, 45, 0} },
    { 43, 8, 0x31, {1, 3, 7, 3, 25, 31, 65, 79, 0} },
    { 44, 8, 0x32, {1, 3, 1, 1, 19, 11, 3, 205, 0} },
    { 45, 8, 0x34, {1, 1, 5, 9, 19, 21, 29, 157, 0} },
    { 46, 8, 0x38, {1, 3, 7, 11, 1, 33, 89, 185, 0} },
    { 47, 8, 0x43, {1, 3, 3, 3, 15, 9, 79, 71, 0} },
    { 48, 8, 0x46, {1, 3, 7, 11, 15, 39, 119, 27, 0} },
    { 49, 8, 0x54, {1, 1, 3, 1, 11, 31, 97, 225, 0} },
    { 50, 8, 0x61, {1, 1, 1, 3, 23, 43, 57, 177, 0} },
    { 51, 8, 0x67, {1, 3, 7, 7, 17, 17, 37, 71, 0} },
    { 52, 8, 0x73, {1, 3, 1, 5, 27, 63, 123, 213, 0} },
    { 53, 8, 0x7A, {1, 1, 3, 5, 11, 43, 53, 133, 0} },
    { 54, 9, 0x8, {1, 3, 5, 5, 29, 17, 47, 173, 479} },
    { 55, 9, 0xD, {1, 3, 3, 11, 3, 1, 109, 9, 69} },
    { 56, 9, 0x10, {1, 1, 1, 5, 17, 39, 23, 5, 343} },
    { 57, 9, 0x16, {1, 3, 1, 5, 25, 15, 31, 103, 499} },
    { 58, 9, 0x19, {1, 1, 1, 11, 11, 17, 63, 105, 183} },
    { 59, 9, 0x2C, {1, 1, 5, 11, 9, 29, 97, 231, 363} },
    { 60, 9, 0x2F, {1, 1, 5, 15, 19, 45, 41, 7, 383} },
    { 61, 9, 0x34, {1, 3, 7, 7, 31, 19, 83, 137, 221} },
    { 62, 9, 0x37, {1, 1, 1, 3, 23, 15, 111, 223, 83} },
    { 63, 9, 0x3B, {1, 1, 5, 13, 31, 15, 55, 25, 161} },
    { 64, 9, 0x3E, {1, 1, 3, 13, 25, 47, 39, 87, 257} },
};

constexpr double kReciprocalPow53 = 1.0 / 9007199254740992.0; // 2^53

} // namespace

SobolSequence::SobolSequence(std::size_t dimension,
                             bool scrambled,
                             std::uint64_t seed)
    : dimension_(dimension),
      directions_(dimension),
      scramble_(dimension, 0) {
    if (dimension == 0 || dimension > kMaxSupportedDimension) {
        throw std::invalid_argument("SobolSequence: unsupported dimension");
    }

    for (std::size_t dim = 0; dim < dimension_; ++dim) {
        const SobolDirection& data = kSobolData[dim];
        auto& row = directions_[dim].values;
        row.fill(0);

        const unsigned s = data.s;
        const unsigned a = data.a;
        for (unsigned i = 0; i < s; ++i) {
            row[i] = static_cast<std::uint64_t>(data.m[i])
                     << (kMaxBits - (i + 1));
        }
        for (unsigned i = s; i < kMaxBits; ++i) {
            std::uint64_t value = row[i - s] ^ (row[i - s] >> s);
            for (unsigned k = 1; k < s; ++k) {
                if ((a >> (s - 1 - k)) & 1U) {
                    value ^= row[i - k];
                }
            }
            row[i] = value;
        }
    }

    if (scrambled) {
        std::mt19937_64 rng(seed ? seed : 0x9E3779B97F4A7C15ULL);
        for (std::size_t dim = 0; dim < dimension_; ++dim) {
            scramble_[dim] = rng();
        }
    }
}

void SobolSequence::generate(std::uint64_t index, double* out) const {
    for (std::size_t dim = 0; dim < dimension_; ++dim) {
        std::uint64_t value = 0;
        std::uint64_t i = index;
        unsigned bit = 0;
        while (i) {
            if (i & 1ULL) {
                value ^= directions_[dim].values[bit];
            }
            i >>= 1;
            ++bit;
        }
        if (scramble_[dim] != 0) {
            value ^= scramble_[dim];
        }
        double u = (static_cast<double>(value >> 11) + 0.5) * kReciprocalPow53;
        out[dim] = std::min(1.0 - std::numeric_limits<double>::epsilon(), std::max(u, std::numeric_limits<double>::min()));
    }
}

std::vector<double> SobolSequence::generate(std::uint64_t index) const {
    std::vector<double> result(dimension_);
    generate(index, result.data());
    return result;
}

} // namespace quant::qmc
