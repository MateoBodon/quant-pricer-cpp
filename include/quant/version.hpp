// Quant pricer version utilities
#pragma once

#include <string>

namespace quant {

constexpr int kVersionMajor = 0;
constexpr int kVersionMinor = 1;
constexpr int kVersionPatch = 0;

inline std::string version_string() {
    return std::to_string(kVersionMajor) + "." +
           std::to_string(kVersionMinor) + "." +
           std::to_string(kVersionPatch);
}

}  // namespace quant


