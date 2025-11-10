.PHONY: bench

bench:
	cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
	cmake --build build --parallel
	cmake --build build --target bench
