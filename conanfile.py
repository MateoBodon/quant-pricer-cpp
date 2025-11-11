from conan import ConanFile
from conan.tools.cmake import CMake, cmake_layout


class QuantPricerRecipe(ConanFile):
    name = "quant-pricer-cpp"
    version = "0.2.0"
    license = "MIT"
    url = "https://github.com/MateoBodon/quant-pricer-cpp"
    description = "C++20 option pricing: Black-Scholes, MC, PDE, barriers, Heston"
    settings = "os", "compiler", "build_type", "arch"
    options = {"with_openmp": [True, False]}
    default_options = {"with_openmp": True}
    exports_sources = (
        "CMakeLists.txt",
        "cmake/*",
        "include/*",
        "src/*",
        "external/*",
        "tests/*",
        "benchmarks/*",
    )

    def layout(self):
        cmake_layout(self)

    def generate(self):
        pass

    def build(self):
        cmake = CMake(self)
        defs = {}
        if self.options.with_openmp:
            defs["QUANT_ENABLE_OPENMP"] = "ON"
        cmake.configure(variables=defs)
        cmake.build()

    def package(self):
        cmake = CMake(self)
        cmake.install()

    def package_info(self):
        self.cpp_info.libs = ["quant_pricer"]
