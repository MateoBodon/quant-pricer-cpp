cmake_minimum_required(VERSION 3.16)
project(quant_pricer_cpp VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)


# Dependencies: prefer submodules in external/, fallback to FetchContent if missing
set(GTEST_SOURCE_DIR ${CMAKE_SOURCE_DIR}/external/googletest)
set(BENCH_SOURCE_DIR ${CMAKE_SOURCE_DIR}/external/benchmark)

if(EXISTS ${GTEST_SOURCE_DIR}/CMakeLists.txt)
  message(STATUS "Using submodule: GoogleTest")
  add_subdirectory(${GTEST_SOURCE_DIR} external/googletest-build)
else()
  include(FetchContent)
  FetchContent_Declare(
    googletest
    URL https://github.com/google/googletest/archive/refs/tags/v1.14.0.zip
  )
  set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
  FetchContent_MakeAvailable(googletest)
endif()

if(EXISTS ${BENCH_SOURCE_DIR}/CMakeLists.txt)
  message(STATUS "Using submodule: Google Benchmark")
  add_subdirectory(${BENCH_SOURCE_DIR} external/benchmark-build)
else()
  include(FetchContent)
  FetchContent_Declare(
    googlebenchmark
    URL https://github.com/google/benchmark/archive/refs/tags/v1.8.3.zip
  )
  set(BENCHMARK_ENABLE_GTEST_TESTS OFF CACHE BOOL "" FORCE)
  set(BENCHMARK_ENABLE_TESTING OFF CACHE BOOL "" FORCE)
  FetchContent_MakeAvailable(googlebenchmark)
endif()

# Options
option(QUANT_ENABLE_OPENMP "Enable OpenMP parallelization" ON)

# OpenMP
if(QUANT_ENABLE_OPENMP)
  find_package(OpenMP)
  if(OpenMP_CXX_FOUND)
    message(STATUS "OpenMP found: enabling")
    set(HAS_OPENMP ON)
  else()
    message(STATUS "OpenMP not found: continuing without")
    set(HAS_OPENMP OFF)
  endif()
endif()

# Library target (will grow with pricers)
add_library(quant_pricer
  src/version.cpp
)

target_include_directories(quant_pricer PUBLIC include)

if(HAS_OPENMP)
  target_compile_definitions(quant_pricer PUBLIC QUANT_HAS_OPENMP=1)
  target_link_libraries(quant_pricer PUBLIC OpenMP::OpenMP_CXX)
endif()

# Executable for CLI (placeholder)
add_executable(quant_cli src/main.cpp)
target_link_libraries(quant_cli PRIVATE quant_pricer)

# Tests
enable_testing()
add_executable(unit_tests tests/test_sanity.cpp)
target_link_libraries(unit_tests PRIVATE quant_pricer GTest::gtest_main)
include(GoogleTest)
gtest_discover_tests(unit_tests)

# Benchmarks
add_executable(micro_bench benchmarks/bench_sanity.cpp)
target_link_libraries(micro_bench PRIVATE quant_pricer benchmark::benchmark)