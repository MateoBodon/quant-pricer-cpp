#include <quant/black_scholes.hpp>
#include <iostream>
int main(){
  std::cout << quant::bs::call_price(100,100,0.03,0.01,0.2,1) << "\n";
  return 0;
}

