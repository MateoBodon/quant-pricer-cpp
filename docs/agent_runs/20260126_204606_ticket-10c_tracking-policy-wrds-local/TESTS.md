# Tests

- python3 -m venv .venv && . .venv/bin/activate && python -m pip install -r requirements-dev.txt && cmake -S . -B build -DCMAKE_BUILD_TYPE=Release -DPython3_EXECUTABLE=$PWD/.venv/bin/python3 && cmake --build build -j && PATH=$PWD/.venv/bin:$PATH ctest --test-dir build -L FAST --output-on-failure (pass)
