#include <iostream>
#include "quant/version.hpp"

int main() {
    std::cout << "quant-pricer-cpp: " << quant::version_string() << "\n";
    return 0;
}
