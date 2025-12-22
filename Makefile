.PHONY: bench gpt-bundle

bench:
	cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
	cmake --build build --parallel
	cmake --build build --target bench

gpt-bundle:
	python3 scripts/gpt_bundle.py --ticket $(TICKET) --run-name $(RUN_NAME)
