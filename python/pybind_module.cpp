#include <pybind11/pybind11.h>
#include <pybind11/stl.h>

#include "quant/black_scholes.hpp"
#include "quant/mc.hpp"
#include "quant/pde.hpp"

namespace py = pybind11;

PYBIND11_MODULE(pyquant_pricer, m) {
    m.doc() = "Python bindings for quant-pricer-cpp (subset)";

    m.def("bs_call", &quant::bs::call_price, "Black-Scholes call price",
          py::arg("S"), py::arg("K"), py::arg("r"), py::arg("q"), py::arg("sigma"), py::arg("T"));
    m.def("bs_put", &quant::bs::put_price, "Black-Scholes put price",
          py::arg("S"), py::arg("K"), py::arg("r"), py::arg("q"), py::arg("sigma"), py::arg("T"));
}


