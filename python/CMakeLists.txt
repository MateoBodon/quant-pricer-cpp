cmake_minimum_required(VERSION 3.16)

if(NOT TARGET quant_pricer)
  message(FATAL_ERROR "quant_pricer target not found; build root project with -DQUANT_ENABLE_PYBIND=ON")
endif()

include(FetchContent)

find_package(pybind11 CONFIG QUIET)
if(NOT pybind11_FOUND)
  FetchContent_Declare(
    pybind11
    URL https://github.com/pybind/pybind11/archive/refs/tags/v2.11.1.zip
  )
  FetchContent_MakeAvailable(pybind11)
endif()

find_package(Python3 REQUIRED COMPONENTS Interpreter Development.Module)

pybind11_add_module(pyquant_pricer MODULE pybind_module.cpp)
target_link_libraries(pyquant_pricer PRIVATE quant_pricer)
target_compile_features(pyquant_pricer PRIVATE cxx_std_20)

install(
  TARGETS pyquant_pricer
  LIBRARY DESTINATION .
  RUNTIME DESTINATION .
  ARCHIVE DESTINATION .
)
