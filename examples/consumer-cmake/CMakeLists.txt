cmake_minimum_required(VERSION 3.20)
project(qp_consumer CXX)
find_package(quant-pricer CONFIG REQUIRED)
add_executable(probe main.cpp)
target_link_libraries(probe PRIVATE quant_pricer)

