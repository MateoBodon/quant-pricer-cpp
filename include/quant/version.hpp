/// Quant pricer version utilities
#pragma once

#include <string>

namespace quant {

/// Project semantic version components
constexpr int kVersionMajor = 0;
/// Minor version
constexpr int kVersionMinor = 3;
/// Patch version
constexpr int kVersionPatch = 0;

/// Return the semantic version string "major.minor.patch".
inline std::string version_string() {
    return std::to_string(kVersionMajor) + "." +
           std::to_string(kVersionMinor) + "." +
           std::to_string(kVersionPatch);
}

}  // namespace quant
