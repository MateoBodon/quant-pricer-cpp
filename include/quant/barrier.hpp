/// Barrier option primitives and configuration
#pragma once

namespace quant {

enum class OptionType { Call, Put };

enum class BarrierType { UpOut, DownOut, UpIn, DownIn };

struct BarrierSpec {
    BarrierType type;
    double B;
    double rebate{0.0};
};

} // namespace quant

