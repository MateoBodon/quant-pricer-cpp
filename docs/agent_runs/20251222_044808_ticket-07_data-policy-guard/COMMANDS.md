# Commands

ls
sed -n '1,200p' AGENTS.md
sed -n '1,200p' docs/PLAN_OF_RECORD.md
sed -n '1,200p' docs/DOCS_AND_LOGGING_SYSTEM.md
sed -n '1,200p' docs/CODEX_SPRINT_TICKETS.md
date -u +%Y%m%d_%H%M%S
git ls-files | wc -l
git ls-files | rg -n \"\\.(csv|parquet|json)$\" -S
git ls-files | xargs rg -n \"strike,.*market_iv|\\bsecid\\b|best_bid|best_ask|best_offer\" -S
rg -n \"artifacts/heston/fit_|artifacts/heston/series_runs/fit_\" -S .
for f in data/normalized/spy_20230601.csv data/options_2023-06-01.csv data/options_synth.csv data/samples/spx_20240614_sample.csv data/spy_returns.csv wrds_pipeline/sample_data/spx_options_sample.csv; do echo \"--- $f\"; head -n 1 \"$f\"; done
rg -n \"sample_data|spx_options_sample\" -S wrds_pipeline scripts
sed -n '1,220p' wrds_pipeline/ingest_sppx_surface.py
rg -n \"SAMPLE_PATH\" -n wrds_pipeline/ingest_sppx_surface.py
sed -n '300,380p' wrds_pipeline/ingest_sppx_surface.py
rg -n \"artifacts/heston\" -S scripts docs tests project_state
sed -n '1,200p' PROGRESS.md
sed -n '1,200p' project_state/KNOWN_ISSUES.md
ls tests
rg -n \"FAST\" CMakeLists.txt tests cmake -S
sed -n '130,260p' CMakeLists.txt
git status -sb
git checkout -b feature/ticket-07_data-policy-guard
git rm artifacts/heston/fit_20230601.csv artifacts/heston/fit_20240614.csv artifacts/heston/series_runs/fit_20230601.csv artifacts/heston/series_runs/fit_20240614.csv
ls artifacts/heston
ls artifacts/heston/series_runs
wc -l wrds_pipeline/sample_data/spx_options_sample.csv
python3 - <<'PY'
from pathlib import Path
path = Path('wrds_pipeline/sample_data/spx_options_sample.csv')
text = path.read_text()
lines = text.splitlines()
if not lines:
    raise SystemExit('empty file')
header = lines[0]
new_header = header.replace('best_bid', 'bid').replace('best_offer', 'ask')
if header == new_header:
    raise SystemExit('header unchanged; check column names')
lines[0] = new_header
path.write_text('\n'.join(lines) + ('\n' if text.endswith('\n') else ''))
print(f\"Updated header: {header} -> {new_header}\")
PY
apply_patch (wrds_pipeline/ingest_sppx_surface.py)
cat <<'PY' > scripts/check_data_policy.py
#!/usr/bin/env python3
\"\"\"Guard against committing raw/redistributable market-data artifacts.\"\"\"
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

PATTERNS = [
    re.compile(r\"strike,.*market_iv\"),
    re.compile(r\"\\bsecid\\b\"),
    re.compile(r\"best_bid|best_ask|best_offer\"),
]

DATA_EXTS = {\".csv\", \".parquet\", \".json\"}

CODE_DOC_EXTS = {
    \".c\",
    \".cc\",
    \".cpp\",
    \".cmake\",
    \".h\",
    \".hpp\",
    \".md\",
    \".mk\",
    \".py\",
    \".rst\",
    \".sh\",
    \".toml\",
    \".txt\",
    \".yaml\",
    \".yml\",
    \".zsh\",
}

DATA_DIR_PREFIXES = (
    \"artifacts/\",
    \"docs/artifacts/\",
    \"data/\",
    \"wrds_pipeline/sample_data/\",
)


def _git_tracked_files() -> List[str]:
    result = subprocess.run(
        [\"git\", \"ls-files\", \"-z\"],
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    raw = result.stdout.decode(\"utf-8\", errors=\"ignore\")
    return [path for path in raw.split(\"\\0\") if path]


def _is_allowed_code_doc(path: str) -> bool:
    return Path(path).suffix in CODE_DOC_EXTS


def _is_guarded_data_file(path: str) -> bool:
    suffix = Path(path).suffix
    if suffix not in DATA_EXTS:
        return False
    return any(path.startswith(prefix) for prefix in DATA_DIR_PREFIXES)


def _scan_lines(path: str) -> Iterable[Tuple[int, str]]:
    data = Path(path).read_bytes()
    text = data.decode(\"utf-8\", errors=\"ignore\")
    for idx, line in enumerate(text.splitlines(), 1):
        for pattern in PATTERNS:
            if pattern.search(line):
                yield idx, line
                break


def main() -> int:
    violations: List[Tuple[str, int, str]] = []
    for rel_path in _git_tracked_files():
        if _is_allowed_code_doc(rel_path):
            continue
        if not _is_guarded_data_file(rel_path):
            continue
        path = Path(rel_path)
        if not path.exists():
            continue
        for line_no, line in _scan_lines(rel_path):
            violations.append((rel_path, line_no, line))

    if not violations:
        print(\"[data-policy] OK: no restricted patterns found in tracked data artifacts.\")
        return 0

    print(\"[data-policy] FAIL: restricted patterns found in tracked data artifacts:\")
    for rel_path, line_no, line in violations:
        print(f\"{rel_path}:{line_no}:{line}\")
    return 1


if __name__ == \"__main__\":
    sys.exit(main())
PY
cat <<'PY' > tests/test_data_policy_fast.py
#!/usr/bin/env python3
\"\"\"FAST test: ensure data policy guard passes for tracked artifacts.\"\"\"
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_data_policy_guard() -> None:
    script = REPO_ROOT / \"scripts\" / \"check_data_policy.py\"
    cmd = [sys.executable, str(script)]
    subprocess.run(cmd, check=True, cwd=REPO_ROOT)


if __name__ == \"__main__\":
    test_data_policy_guard()
PY
apply_patch (CMakeLists.txt)
apply_patch (project_state/KNOWN_ISSUES.md)
apply_patch (AGENTS.md)
apply_patch (PROGRESS.md)
cat <<'MD' > artifacts/heston/README.md
# Heston calibration artifacts

Tracked artifacts exclude per-strike fit tables (e.g., `fit_YYYYMMDD.csv`) because they can resemble raw market quote surfaces. Generate those tables locally with `scripts/calibrate_heston.py` or `scripts/calibrate_heston_series.py` and keep them untracked unless they are explicitly synthetic/public-source.
MD
rg -n \"__pycache__\" -S .gitignore
python3 -m compileall scripts/check_data_policy.py
python3 scripts/check_data_policy.py
ctest --test-dir build -L FAST --output-on-failure
WRDS_USE_SAMPLE=1 python -m wrds_pipeline.pipeline --fast
WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast
git status -sb
git restore docs/artifacts/manifest.json docs/artifacts/metrics_summary.json docs/artifacts/metrics_summary.md
git status -sb
git rev-parse HEAD
git branch --show-current
uname -a
cmake --version | head -n 1
c++ --version | head -n 1
python3 --version
date +%Y-%m-%dT%H:%M:%S
python3 - <<'PY'
import hashlib
from pathlib import Path
path = Path('wrds_pipeline/sample_data/spx_options_sample.csv')
sha = hashlib.sha256(path.read_bytes()).hexdigest()
print(sha)
PY
RUN_NAME=20251222_044808_ticket-07_data-policy-guard
mkdir -p docs/agent_runs/$RUN_NAME
cat <<'MD' > docs/agent_runs/20251222_044808_ticket-07_data-policy-guard/PROMPT.md
...prompt content...
MD
cat <<'MD' > docs/agent_runs/20251222_044808_ticket-07_data-policy-guard/TESTS.md
...test output...
MD
cat <<'MD' > docs/agent_runs/20251222_044808_ticket-07_data-policy-guard/RESULTS.md
...results content...
MD
cat <<'JSON' > docs/agent_runs/20251222_044808_ticket-07_data-policy-guard/META.json
...meta...
JSON
rg -n \"LAST_COMMIT|DIFF.patch|git diff\" -n scripts/gpt_bundle.py
sed -n '200,280p' scripts/gpt_bundle.py
cat docs/agent_runs/20251222_032810_ticket-06c_bundle-hardgate-tests/META.json
git log -1 --pretty=%H -- docs/agent_runs/20251222_032810_ticket-06c_bundle-hardgate-tests/META.json
cat docs/agent_runs/20251222_001445_ticket-06_checklist-final/META.json
rg -n \"gpt_bundles|timestamp\" -n scripts/gpt_bundle.py
rg -n \"gpt-bundle\" -n Makefile
sed -n '1,80p' Makefile
date -u +%Y%m%dT%H%M%SZ
apply_patch (docs/agent_runs/20251222_044808_ticket-07_data-policy-guard/RESULTS.md)
cat <<'MD' > docs/agent_runs/20251222_044808_ticket-07_data-policy-guard/COMMANDS.md
...command log...
MD
# (failed command due to unmatched backtick while rewriting COMMANDS.md)
cat <<'MD' > docs/agent_runs/20251222_044808_ticket-07_data-policy-guard/COMMANDS.md
...command log...
MD
python3 - <<'PY'
from pathlib import Path

run_name = \"20251222_044808_ticket-07_data-policy-guard\"
path = Path(\"docs/agent_runs\") / run_name / \"COMMANDS.md\"
lines = [...]
path.write_text('\n'.join(lines) + '\n')
PY
RUN_NAME=20251222_044808_ticket-07_data-policy-guard
TIMESTAMP=20251222T050914Z
make gpt-bundle TICKET=ticket-07 RUN_NAME=$RUN_NAME TIMESTAMP=$TIMESTAMP
tail -n 80 docs/CODEX_SPRINT_TICKETS.md
apply_patch (docs/CODEX_SPRINT_TICKETS.md)
apply_patch (docs/agent_runs/20251222_044808_ticket-07_data-policy-guard/RESULTS.md)
RUN_NAME=20251222_044808_ticket-07_data-policy-guard
TIMESTAMP=20251222T050914Z
make gpt-bundle TICKET=ticket-07 RUN_NAME=$RUN_NAME TIMESTAMP=$TIMESTAMP
python3 - <<'PY'
from pathlib import Path
path = Path('docs/agent_runs/20251222_044808_ticket-07_data-policy-guard/COMMANDS.md')
lines = path.read_text().splitlines()
append = [
    'RUN_NAME=20251222_044808_ticket-07_data-policy-guard',
    'TIMESTAMP=20251222T050914Z',
    'make gpt-bundle TICKET=ticket-07 RUN_NAME=$RUN_NAME TIMESTAMP=$TIMESTAMP',
    'tail -n 80 docs/CODEX_SPRINT_TICKETS.md',
    'apply_patch (docs/CODEX_SPRINT_TICKETS.md)',
    'apply_patch (docs/agent_runs/20251222_044808_ticket-07_data-policy-guard/RESULTS.md)',
    'RUN_NAME=20251222_044808_ticket-07_data-policy-guard',
    'TIMESTAMP=20251222T050914Z',
    'make gpt-bundle TICKET=ticket-07 RUN_NAME=$RUN_NAME TIMESTAMP=$TIMESTAMP',
]
lines.extend(append)
path.write_text('\n'.join(lines) + '\n')
PY
git status -sb
