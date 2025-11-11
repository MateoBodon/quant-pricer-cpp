cmake_minimum_required(VERSION 3.16)
project(quant_pricer_cpp VERSION 0.3.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

include(GNUInstallDirs)
include(CMakePackageConfigHelpers)


# Dependencies: prefer submodules in external/, fallback to FetchContent if missing
set(GTEST_SOURCE_DIR ${CMAKE_SOURCE_DIR}/external/googletest)
set(BENCH_SOURCE_DIR ${CMAKE_SOURCE_DIR}/external/benchmark)

if(EXISTS ${GTEST_SOURCE_DIR}/CMakeLists.txt)
  message(STATUS "Using submodule: GoogleTest")
  set(INSTALL_GTEST OFF CACHE BOOL "" FORCE)
  set(INSTALL_GMOCK OFF CACHE BOOL "" FORCE)
  add_subdirectory(${GTEST_SOURCE_DIR} external/googletest-build)
else()
  include(FetchContent)
  FetchContent_Declare(
    googletest
    URL https://github.com/google/googletest/archive/refs/tags/v1.14.0.zip
  )
  set(gtest_force_shared_crt ON CACHE BOOL "" FORCE)
  set(INSTALL_GTEST OFF CACHE BOOL "" FORCE)
  set(INSTALL_GMOCK OFF CACHE BOOL "" FORCE)
  FetchContent_MakeAvailable(googletest)
endif()

if(EXISTS ${BENCH_SOURCE_DIR}/CMakeLists.txt)
  message(STATUS "Using submodule: Google Benchmark")
  set(BENCHMARK_ENABLE_INSTALL OFF CACHE BOOL "" FORCE)
  set(BENCHMARK_ENABLE_GTEST_TESTS OFF CACHE BOOL "" FORCE)
  set(BENCHMARK_ENABLE_TESTING OFF CACHE BOOL "" FORCE)
  add_subdirectory(${BENCH_SOURCE_DIR} external/benchmark-build)
else()
  include(FetchContent)
  FetchContent_Declare(
    googlebenchmark
    URL https://github.com/google/benchmark/archive/refs/tags/v1.8.3.zip
  )
  set(BENCHMARK_ENABLE_GTEST_TESTS OFF CACHE BOOL "" FORCE)
  set(BENCHMARK_ENABLE_TESTING OFF CACHE BOOL "" FORCE)
  set(BENCHMARK_ENABLE_INSTALL OFF CACHE BOOL "" FORCE)
  FetchContent_MakeAvailable(googlebenchmark)
endif()

# Options
option(QUANT_ENABLE_OPENMP "Enable OpenMP parallelization" ON)
option(QUANT_ENABLE_SANITIZERS "Enable Address/UB Sanitizers in supported compilers" OFF)
option(QUANT_ENABLE_CLANG_TIDY "Enable clang-tidy static analysis (if available)" OFF)
option(QUANT_ENABLE_PYBIND "Build Python bindings" OFF)

find_package(Python3 REQUIRED COMPONENTS Interpreter)

# OpenMP
set(HAS_OPENMP OFF)
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

# Static analysis (clang-tidy)
if(QUANT_ENABLE_CLANG_TIDY)
  find_program(CLANG_TIDY_EXE NAMES clang-tidy)
  if(CLANG_TIDY_EXE)
    message(STATUS "clang-tidy enabled: ${CLANG_TIDY_EXE}")
    set(CMAKE_CXX_CLANG_TIDY ${CLANG_TIDY_EXE})
  else()
    message(WARNING "clang-tidy requested but not found")
  endif()
endif()

# Sanitizers
set(SANITIZER_COMPILE_FLAGS "")
set(SANITIZER_LINK_FLAGS "")
if(QUANT_ENABLE_SANITIZERS AND (CMAKE_CXX_COMPILER_ID MATCHES "Clang|GNU"))
  set(SANITIZER_COMPILE_FLAGS "-fsanitize=address" "-fsanitize=undefined" "-fno-omit-frame-pointer")
  set(SANITIZER_LINK_FLAGS "-fsanitize=address" "-fsanitize=undefined")
  message(STATUS "Sanitizers enabled: ${SANITIZER_COMPILE_FLAGS}")
endif()

# Library target (will grow with pricers)
add_library(quant_pricer
  src/version.cpp
  src/black_scholes.cpp
  src/mc.cpp
  src/pde.cpp
  src/grid_utils.cpp
  src/bs_barrier_rr.cpp
  src/mc_barrier.cpp
  src/pde_barrier.cpp
  src/american.cpp
  src/qmc/sobol.cpp
  src/qmc/brownian_bridge.cpp
  src/digital.cpp
  src/asian.cpp
  src/lookback.cpp
  src/heston.cpp
  src/risk.cpp
  src/multi.cpp
)

add_library(quant_pricer::quant_pricer ALIAS quant_pricer)

target_compile_features(quant_pricer PUBLIC cxx_std_20)

target_include_directories(quant_pricer
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_SOURCE_DIR}/include>
    $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}>
    $<BUILD_INTERFACE:${CMAKE_SOURCE_DIR}/external/pcg/include>
    $<INSTALL_INTERFACE:${CMAKE_INSTALL_INCLUDEDIR}/pcg>
)

if(HAS_OPENMP)
  target_compile_definitions(quant_pricer PUBLIC QUANT_HAS_OPENMP=1)
  target_link_libraries(quant_pricer PUBLIC OpenMP::OpenMP_CXX)
endif()

# Executable for CLI (placeholder)
add_executable(quant_cli src/main.cpp)
target_link_libraries(quant_cli PRIVATE quant_pricer)

# Tests
enable_testing()
add_executable(unit_tests
  tests/test_sanity.cpp
  tests/test_black_scholes.cpp
  tests/test_mc.cpp
  tests/test_pde.cpp
  tests/test_barrier.cpp
  tests/test_american.cpp
  tests/test_grid_utils.cpp
  tests/test_digital.cpp
  tests/test_asian.cpp
  tests/test_term_structures.cpp
  tests/test_multi.cpp
  tests/test_barrier_mc_regression.cpp
  tests/test_risk.cpp
  tests/test_heston.cpp
  tests/test_rng_repro.cpp)
target_sources(unit_tests PRIVATE tests/test_lookback.cpp)
target_link_libraries(unit_tests PRIVATE quant_pricer GTest::gtest_main)
include(GoogleTest)
gtest_add_tests(TARGET unit_tests TEST_LIST unit_test_list)

foreach(test_name ${unit_test_list})
  if(test_name MATCHES "^.*Slow\\.")
    set_tests_properties(${test_name} PROPERTIES LABELS "SLOW")
  elseif(test_name MATCHES "^.*Fast\\.")
    set_tests_properties(${test_name} PROPERTIES LABELS "FAST")
  else()
    set_tests_properties(${test_name} PROPERTIES LABELS "FAST")
  endif()
endforeach()

# Benchmarks
add_executable(micro_bench benchmarks/bench_sanity.cpp)
target_link_libraries(micro_bench PRIVATE quant_pricer benchmark::benchmark)

add_executable(bench_mc benchmarks/bench_mc.cpp)
target_link_libraries(bench_mc PRIVATE quant_pricer benchmark::benchmark)

add_executable(bench_pde benchmarks/bench_pde.cpp)
target_link_libraries(bench_pde PRIVATE quant_pricer benchmark::benchmark)

add_test(NAME bench_micro COMMAND micro_bench --benchmark_min_time=0.01 --benchmark_repetitions=1 --benchmark_format=json)
add_test(NAME bench_mc_run COMMAND bench_mc --benchmark_min_time=0.01 --benchmark_repetitions=1 --benchmark_format=json)
add_test(NAME bench_pde_run COMMAND bench_pde --benchmark_min_time=0.01 --benchmark_repetitions=1 --benchmark_format=json)
set_tests_properties(bench_micro PROPERTIES LABELS "BENCH" RESOURCE_LOCK CPU)
set_tests_properties(bench_mc_run PROPERTIES LABELS "BENCH" RESOURCE_LOCK CPU)
set_tests_properties(bench_pde_run PROPERTIES LABELS "BENCH" RESOURCE_LOCK CPU)

add_custom_target(bench
  COMMAND ${CMAKE_CTEST_COMMAND} --output-on-failure -L BENCH
  DEPENDS micro_bench bench_mc bench_pde
  WORKING_DIRECTORY ${CMAKE_BINARY_DIR}
  COMMENT "Run benchmark suite (label=BENCH)")

add_test(
  NAME heston_calibration_fast
  COMMAND ${Python3_EXECUTABLE} ${CMAKE_SOURCE_DIR}/tests/test_heston_fast.py
)
set_tests_properties(heston_calibration_fast PROPERTIES LABELS "FAST")

add_test(
  NAME qmc_vs_prng_equal_time_fast
  COMMAND ${Python3_EXECUTABLE} ${CMAKE_SOURCE_DIR}/tests/test_qmc_fast.py
)
set_tests_properties(qmc_vs_prng_equal_time_fast PROPERTIES LABELS "FAST")

add_test(
  NAME greeks_reliability_fast
  COMMAND ${Python3_EXECUTABLE} ${CMAKE_SOURCE_DIR}/tests/test_greeks_reliability_fast.py
)
set_tests_properties(greeks_reliability_fast PROPERTIES LABELS "FAST")

add_test(
  NAME heston_series_fast
  COMMAND ${Python3_EXECUTABLE} ${CMAKE_SOURCE_DIR}/tests/test_heston_series_fast.py
)
set_tests_properties(heston_series_fast PROPERTIES LABELS "FAST")

add_test(
  NAME parity_checks_fast
  COMMAND ${Python3_EXECUTABLE} ${CMAKE_SOURCE_DIR}/tests/test_parity_fast.py
)
set_tests_properties(parity_checks_fast PROPERTIES LABELS "FAST")

add_test(
  NAME heston_safety_fast
  COMMAND ${Python3_EXECUTABLE} ${CMAKE_SOURCE_DIR}/tests/test_heston_safety_fast.py
)
set_tests_properties(heston_safety_fast PROPERTIES LABELS "FAST")

add_test(
  NAME market_wrds_pipeline
  COMMAND ${Python3_EXECUTABLE} ${CMAKE_SOURCE_DIR}/wrds_pipeline/tests/test_wrds_pipeline.py
)
set_tests_properties(market_wrds_pipeline PROPERTIES LABELS "MARKET" SKIP_RETURN_CODE 77)

# Apply sanitizer flags to targets if requested
if(SANITIZER_COMPILE_FLAGS OR SANITIZER_LINK_FLAGS)
  foreach(tgt IN ITEMS quant_pricer quant_cli unit_tests micro_bench bench_mc bench_pde)
    if(TARGET ${tgt})
      if(SANITIZER_COMPILE_FLAGS)
        target_compile_options(${tgt} PRIVATE ${SANITIZER_COMPILE_FLAGS})
      endif()
      if(SANITIZER_LINK_FLAGS)
        target_link_options(${tgt} PRIVATE ${SANITIZER_LINK_FLAGS})
      endif()
    endif()
endforeach()
endif()

if(QUANT_ENABLE_PYBIND)
  add_subdirectory(python)
endif()

# Install/export package metadata
set(QUANT_PRICER_HAS_OPENMP ${HAS_OPENMP})

install(TARGETS quant_pricer quant_cli
  EXPORT quant_pricerTargets
  ARCHIVE DESTINATION ${CMAKE_INSTALL_LIBDIR}
  LIBRARY DESTINATION ${CMAKE_INSTALL_LIBDIR}
  RUNTIME DESTINATION ${CMAKE_INSTALL_BINDIR}
  INCLUDES DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
)

install(DIRECTORY include/
        DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}
        PATTERN ".DS_Store" EXCLUDE)
if(EXISTS ${CMAKE_SOURCE_DIR}/external/pcg/include)
  install(DIRECTORY ${CMAKE_SOURCE_DIR}/external/pcg/include/
          DESTINATION ${CMAKE_INSTALL_INCLUDEDIR}/pcg
          PATTERN ".DS_Store" EXCLUDE)
endif()

install(EXPORT quant_pricerTargets
  FILE quant-pricer-targets.cmake
  NAMESPACE quant_pricer::
  DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/quant-pricer
)

configure_package_config_file(
  ${CMAKE_SOURCE_DIR}/cmake/quant-pricer-config.cmake.in
  ${CMAKE_CURRENT_BINARY_DIR}/quant-pricer-config.cmake
  INSTALL_DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/quant-pricer
)

write_basic_package_version_file(
  ${CMAKE_CURRENT_BINARY_DIR}/quant-pricer-config-version.cmake
  VERSION ${PROJECT_VERSION}
  COMPATIBILITY SameMajorVersion
)

install(FILES
  ${CMAKE_CURRENT_BINARY_DIR}/quant-pricer-config.cmake
  ${CMAKE_CURRENT_BINARY_DIR}/quant-pricer-config-version.cmake
  DESTINATION ${CMAKE_INSTALL_LIBDIR}/cmake/quant-pricer
)
