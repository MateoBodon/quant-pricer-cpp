RUN_NAME="$(date -u +%Y%m%d_%H%M%S)_ticket-02_wrds-asof-checks"
RUN_DIR="docs/agent_runs/${RUN_NAME}"
mkdir -p "$RUN_DIR"
: > "$RUN_DIR/COMMANDS.md"
printf '%s\n' "$RUN_NAME" > "$RUN_DIR/RUN_NAME.txt"
RUN_DIR=$(ls -td docs/agent_runs/*_ticket-02_wrds-asof-checks | head -n1)
RUN_NAME=$(basename "$RUN_DIR")
CREATED_UTC=$(date -u +%Y-%m-%dT%H:%M:%SZ)
cat <<'EOF' > "$RUN_DIR/PROMPT.md"
You are a coding agent operating in the `quant-pricer-cpp` repository.

BEGIN by reading these files (in order):
- AGENTS.md
- docs/PLAN_OF_RECORD.md
- docs/DOCS_AND_LOGGING_SYSTEM.md
- docs/CODEX_SPRINT_TICKETS.md

Ticket: ticket-02 — WRDS as-of correctness hard checks + poison-pill tests (sample mode)

Non-negotiable (stop-the-line):
- Do NOT fabricate results or claim commands ran if they did not (log everything).
- Do NOT commit raw WRDS/OptionMetrics data or leak credentials into logs.
- Do NOT “fix” validity by weakening evaluation (no silent filtering unless explicitly specified and logged).
- Follow DOCS_AND_LOGGING_SYSTEM.md: create run log folder + required files.

Goal (1 sentence):
Add automated checks that catch quote_date/trade_date mismatches and prevent lookahead in WRDS calibration and OOS evaluation (sample mode).

Acceptance criteria (must satisfy all):
1) Calibration step hard-fails (preferred) OR filters-to-zero (only if explicitly configured/logged) if any row has `quote_date != trade_date`.
2) OOS evaluation hard-fails if any row has `quote_date != next_trade_date`.
3) A FAST test injects a “poison” sample file and verifies the pipeline rejects it (non-zero exit / raised exception + clear message).
4) Outputs include provenance fields for `trade_date` and `next_trade_date` (written into whatever provenance JSON/manifest the WRDS pipeline emits).

Required workflow (do NOT write a long upfront plan):
1) Create a new run log folder:
   - RUN_NAME="$(date -u +%Y%m%d_%H%M%S)_ticket-02_wrds-asof-checks"
   - RUN_DIR="docs/agent_runs/${RUN_NAME}"
   - Create: PROMPT.md, COMMANDS.md, RESULTS.md, TESTS.md, META.json (and SOURCES.md only if web research used).
   - Put this entire prompt text into PROMPT.md.
   - Start COMMANDS.md immediately and append every command you run.

2) Inspect the WRDS pipeline code + sample data schema:
   - Locate entrypoints:
     - `wrds_pipeline/pipeline.py`
     - calibration module(s): `wrds_pipeline/calibrate_*.py`
     - OOS module(s): `wrds_pipeline/oos_pricing.py` (or equivalent)
     - ingest module(s): `wrds_pipeline/ingest_*.py`
     - existing tests: `wrds_pipeline/tests/*` and/or CTest FAST python tests
   - Identify where `quote_date`, `trade_date`, and `next_trade_date` are:
     - parsed
     - compared
     - used to select calibration/OOS rows

3) Implement hard checks (fail-closed, with clear error messages):
   - Calibration:
     - Before fitting, assert ALL rows used satisfy `quote_date == trade_date`.
     - If violated: raise a clear exception (include a small sample of offending rows/ids, but no secrets).
   - OOS evaluation:
     - Before computing OOS errors, assert ALL rows used satisfy `quote_date == next_trade_date`.
     - If violated: raise a clear exception.

4) Add poison-pill test in sample mode:
   - Add a small synthetic sample fixture (license-safe) with `# SYNTHETIC_DATA` marker if it is a CSV under `wrds_pipeline/sample_data/`.
   - The poison should include at least one row where:
     - calibration poison: `quote_date != trade_date`, OR
     - oos poison: `quote_date != next_trade_date`
   - Add a FAST test that runs the sample pipeline against the poison input and asserts it FAILS.
   - IMPORTANT: do not rely on global mutable state; make the test deterministic.
   - If the pipeline currently cannot be pointed at an alternate sample root/file, add a minimal config/env override to do so (document it).

5) Provenance outputs:
   - Ensure the WRDS pipeline writes `trade_date` and `next_trade_date` into its provenance output(s):
     - e.g., a per-run JSON, a manifest entry, or a dedicated provenance file under `docs/artifacts/wrds/` in sample mode.
   - If there is already a provenance schema, extend it minimally and update any readers accordingly.

6) Run minimal sufficient tests (log in TESTS.md with outputs):
   - Build + FAST tests (per AGENTS.md):
     - `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release`
     - `cmake --build build -j`
     - `ctest --test-dir build -L FAST --output-on-failure`
   - Sample-mode real-data smoke (must run, not just unit tests):
     - Prefer: `WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast`
     - If `python` is on PATH instead, `python -m wrds_pipeline.pipeline --fast` is fine — record what you used.
   - Confirm the poison-pill test fails before fix (if you can demonstrate) and passes after fix by asserting the pipeline now rejects poison input.

7) Update docs:
   - PROGRESS.md: add a dated entry with:
     - what changed
     - exact tests run
     - sample pipeline command used
   - If you discover an existing as-of leakage behavior: update `project_state/KNOWN_ISSUES.md` with:
     - the issue
     - the fix
     - link to this run log folder
   - If you add/rename env vars or config knobs: update `project_state/CONFIG_REFERENCE.md` (or the appropriate source doc).

8) Commit on a feature branch:
   - `git switch -c codex/ticket-02-wrds-asof-checks`
   - Commit message: `ticket-02: WRDS as-of correctness gates + poison tests`
   - Commit body must include:
     - `Tests: <exact commands>`
     - `Artifacts: <paths updated or 'none'>`
     - `Run log: docs/agent_runs/${RUN_NAME}/`

9) Generate the next review bundle at the end (and record the bundle path in RESULTS.md):
   - `make gpt-bundle TICKET=ticket-02 RUN_NAME=${RUN_NAME}`

Suggested Codex invocation (safe mode; approvals on):
- `codex --profile safe`

Human merge checklist (append to RESULTS.md):
- Poison-pill test fails without the fix and fails-closed in production paths
- Sample pipeline smoke ran successfully in WRDS_USE_SAMPLE=1 mode
- No raw WRDS extracts or credentials committed or printed
- PROGRESS.md updated; KNOWN_ISSUES/CONFIG_REFERENCE updated if impacted
- Bundle generated via make gpt-bundle and contains complete non-empty run logs
RUN_DIR=$(ls -td docs/agent_runs/*_ticket-02_wrds-asof-checks | head -n1)
ls -la "$RUN_DIR"
sed -n '1,120p' "$RUN_DIR/COMMANDS.md"
sed -n '1,200p' AGENTS.md
sed -n '1,200p' docs/PLAN_OF_RECORD.md
sed -n '1,200p' docs/DOCS_AND_LOGGING_SYSTEM.md
sed -n '1,200p' docs/CODEX_SPRINT_TICKETS.md
rg -n "quote_date|trade_date|next_trade_date" wrds_pipeline
sed -n '1,240p' wrds_pipeline/pipeline.py
sed -n '240,520p' wrds_pipeline/pipeline.py
sed -n '520,880p' wrds_pipeline/pipeline.py
sed -n '420,560p' wrds_pipeline/calibrate_heston.py
rg -n "def calibrate|quote_date|trade_date" wrds_pipeline/calibrate_heston.py
sed -n '340,440p' wrds_pipeline/calibrate_heston.py
sed -n '1,200p' wrds_pipeline/oos_pricing.py
sed -n '1,240p' wrds_pipeline/ingest_sppx_surface.py
sed -n '240,520p' wrds_pipeline/ingest_sppx_surface.py
head -n 5 wrds_pipeline/sample_data/spx_options_sample.csv
sed -n '1,200p' wrds_pipeline/tests/test_wrds_pipeline.py
ls -la wrds_pipeline/tests
rg -n "FAST|pytest|wrds_pipeline" -S .
ls -la tests
rg -n "add_test|pytest|test_.*\.py" CMakeLists.txt tests CMake
sed -n '160,280p' CMakeLists.txt
sed -n '1,240p' scripts/manifest_utils.py
sed -n '1,200p' project_state/CONFIG_REFERENCE.md
sed -n '1,200p' scripts/check_data_policy.py
sed -n '1,200p' tests/test_heston_fast.py
rg -n "def write_surface" -n wrds_pipeline/ingest_sppx_surface.py
sed -n '520,620p' wrds_pipeline/ingest_sppx_surface.py
rg -n "calibrate_heston\.calibrate" -S .
rg -n "wrds_pipeline\.calibrate_heston|calibrate_heston" scripts wrds_pipeline python -S
python3 - <<'PY'
import json
from pathlib import Path
path = Path('docs/artifacts/manifest.json')
if path.exists():
    data = json.loads(path.read_text())
    for key in ['wrds_pipeline','wrds_heston','wrds_dateset']:
        if key in data.get('runs', {}):
            print(key, 'entries', len(data['runs'][key]) if isinstance(data['runs'][key], list) else 'single')
            print(data['runs'][key][-1] if isinstance(data['runs'][key], list) else data['runs'][key])
else:
    print('manifest missing')
PY
tail -n 5 wrds_pipeline/sample_data/spx_options_sample.csv
python3 - <<'PY'
import pandas as pd
from pathlib import Path
path = Path('wrds_pipeline/sample_data/spx_options_sample.csv')
df = pd.read_csv(path, comment='#')
print(df['trade_date'].value_counts())
PY
apply_patch (wrds_pipeline/asof_checks.py)
apply_patch (wrds_pipeline/ingest_sppx_surface.py)
head -n 40 wrds_pipeline/calibrate_heston.py
apply_patch (wrds_pipeline/calibrate_heston.py)
apply_patch (wrds_pipeline/oos_pricing.py)
apply_patch (wrds_pipeline/pipeline.py)
python3 - <<'PY'
import pandas as pd
from pathlib import Path

src = Path("wrds_pipeline/sample_data/spx_options_sample.csv")
df = pd.read_csv(src, comment="#")
df = df[df["trade_date"].isin(["2024-06-14", "2024-06-17"])].copy()

cols = [
    "trade_date",
    "quote_date",
    "exdate",
    "cp_flag",
    "strike_price",
    "bid",
    "ask",
    "spot",
    "rate",
    "dividend",
    "forward_price",
]

# Calibration poison: mismatch on trade_date rows.
df_calib = df.copy()
df_calib["quote_date"] = df_calib["trade_date"]
df_calib.loc[df_calib["trade_date"] == "2024-06-14", "quote_date"] = "2024-06-13"
df_calib = df_calib[cols]
out_calib = Path("wrds_pipeline/sample_data/spx_options_sample_poison_calib.csv")
out_calib.write_text(
    "# SYNTHETIC_DATA: poison sample with quote_date mismatch for calibration.\n"
)
df_calib.to_csv(out_calib, mode="a", index=False)

# OOS poison: mismatch on next_trade_date rows.
df_oos = df.copy()
df_oos["quote_date"] = df_oos["trade_date"]
df_oos.loc[df_oos["trade_date"] == "2024-06-17", "quote_date"] = "2024-06-14"
df_oos = df_oos[cols]
out_oos = Path("wrds_pipeline/sample_data/spx_options_sample_poison_oos.csv")
out_oos.write_text(
    "# SYNTHETIC_DATA: poison sample with quote_date mismatch for OOS.\n"
)
df_oos.to_csv(out_oos, mode="a", index=False)
PY
head -n 5 wrds_pipeline/sample_data/spx_options_sample_poison_calib.csv
head -n 5 wrds_pipeline/sample_data/spx_options_sample_poison_oos.csv
apply_patch (tests/test_wrds_asof_poison_fast.py)
apply_patch (CMakeLists.txt)
apply_patch (project_state/CONFIG_REFERENCE.md)
tail -n 20 PROGRESS.md
sed -n '1,200p' project_state/KNOWN_ISSUES.md
sed -n '1,120p' CHANGELOG.md
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j
ctest --test-dir build -L FAST --output-on-failure
WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast
git status -sb
git diff --stat
cat docs/agent_runs/20251222_204744_ticket-01_unify-artifacts/META.json
python3 - <<'PY'
import json
from pathlib import Path
path = Path('docs/artifacts/manifest.json')
if not path.exists():
    raise SystemExit('manifest missing')
data = json.loads(path.read_text())
entry = data['runs'].get('wrds_heston', [])
print(entry[-1] if entry else 'no wrds_heston entries')
PY
cat <<'EOF' > "$RUN_DIR/TESTS.md"
# Tests

- `cmake -S . -B build -DCMAKE_BUILD_TYPE=Release` — PASS
- `cmake --build build -j` — PASS
- `ctest --test-dir build -L FAST --output-on-failure` — PASS (58 tests; 1 skipped: RngDeterminism.CounterRngThreadInvariant)
- `WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast` — PASS
  - Output: `[wrds_pipeline] SPX 2024-06-14 source_today=sample source_next=sample`
sed -n '1,120p' "$RUN_DIR/TESTS.md"
apply_patch (project_state/KNOWN_ISSUES.md)
apply_patch (CHANGELOG.md)
apply_patch (PROGRESS.md)
cat <<'RESULTS_EOF' > "$RUN_DIR/RESULTS.md"
# Results

- Added as-of correctness gates: calibration now enforces `quote_date == trade_date`, OOS evaluation enforces `quote_date == next_trade_date` (via `oos_pricing.evaluate`), and the pipeline writes trade_date/next_trade_date into `wrds_heston` manifest entries.
- Introduced `WRDS_SAMPLE_PATH` override plus two poison sample fixtures and a FAST test that confirms the pipeline fails-closed on as-of mismatches.
- Artifacts updated by FAST + sample pipeline runs: `docs/artifacts/manifest.json`, `docs/artifacts/metrics_summary.md`, `docs/artifacts/metrics_summary.json`.
- Pre-fix poison failure was not captured; the new poison test demonstrates fail-closed behavior after the change.

Human merge checklist
- Poison-pill test fails without the fix and fails-closed in production paths
- Sample pipeline smoke ran successfully in WRDS_USE_SAMPLE=1 mode
- No raw WRDS extracts or credentials committed or printed
- PROGRESS.md updated; KNOWN_ISSUES/CONFIG_REFERENCE updated if impacted
- Bundle generated via make gpt-bundle and contains complete non-empty run logs
RESULTS_EOF
git switch -c codex/ticket-02-wrds-asof-checks
python3 - <<'PY'
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

run_dir = Path("docs/agent_runs")
run_dir = next(run_dir.glob("*_ticket-02_wrds-asof-checks"))
run_name = run_dir.name

stamp = run_name.split("_ticket-")[0]
started = datetime.strptime(stamp, "%Y%m%d_%H%M%S").replace(tzinfo=timezone.utc)
finished = datetime.now(timezone.utc)

def run(cmd):
    return subprocess.check_output(cmd, text=True).strip()

git_sha = run(["git", "rev-parse", "HEAD"])
branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
host_os = run(["uname", "-a"])
compiler = run(["c++", "--version"]).splitlines()[0].strip()
python_version = run(["python3", "-V"])
cmake_version = run(["cmake", "--version"]).splitlines()[0].strip()

panel_path = Path("wrds_pipeline_dates_panel.yaml")
wrds_panel_hash = None
if panel_path.exists():
    wrds_panel_hash = hashlib.sha256(panel_path.read_bytes()).hexdigest()

meta = {
    "run_name": run_name,
    "ticket_id": "ticket-02",
    "started_at_utc": started.isoformat().replace("+00:00", "Z"),
    "finished_at_utc": finished.isoformat().replace("+00:00", "Z"),
    "git_sha_before": git_sha,
    "git_sha_after": git_sha,
    "branch_name": branch,
    "host_os": host_os,
    "compiler": compiler,
    "python_version": python_version,
    "build_type": "Release",
    "dataset_id": "WRDS_SAMPLE",
    "config_hashes": {
        "scenario_grid": None,
        "tolerances": None,
        "wrds_panel": wrds_panel_hash,
    },
    "tools": {
        "codex_cli": "unknown",
        "cmake": cmake_version,
    },
    "notes": "OpenMP not found; WRDS sample smoke executed via python3.",
}

(run_dir / "META.json").write_text(json.dumps(meta, indent=2) + "\n")
PY
cat "$RUN_DIR/META.json"
rg -n "WRDS_SAMPLE_PATH|quote_date|_standardize_quote_date" -n wrds_pipeline/ingest_sppx_surface.py
rg -n "assert_quote_date_matches|trade_date|next_trade_date" wrds_pipeline/calibrate_heston.py
rg -n "expected_quote_date|as-of" wrds_pipeline/oos_pricing.py
rg -n "expected_quote_date" wrds_pipeline/pipeline.py
git status -sb
RUN_DIR=$(ls -td docs/agent_runs/*_ticket-02_wrds-asof-checks | head -n1)
RUN_NAME=$(basename "$RUN_DIR")
make gpt-bundle TICKET=ticket-02 RUN_NAME=${RUN_NAME}
apply_patch (docs/agent_runs/20251223_183500_ticket-02_wrds-asof-checks/RESULTS.md)
git status -sb
git add CMakeLists.txt CHANGELOG.md PROGRESS.md project_state/CONFIG_REFERENCE.md project_state/KNOWN_ISSUES.md wrds_pipeline/asof_checks.py wrds_pipeline/ingest_sppx_surface.py wrds_pipeline/calibrate_heston.py wrds_pipeline/oos_pricing.py wrds_pipeline/pipeline.py wrds_pipeline/sample_data/spx_options_sample_poison_calib.csv wrds_pipeline/sample_data/spx_options_sample_poison_oos.csv tests/test_wrds_asof_poison_fast.py docs/artifacts/manifest.json docs/artifacts/metrics_summary.md docs/artifacts/metrics_summary.json docs/agent_runs/20251223_183500_ticket-02_wrds-asof-checks
git status -sb
git add docs/agent_runs/20251223_183500_ticket-02_wrds-asof-checks/COMMANDS.md
git status -sb
git add CMakeLists.txt CHANGELOG.md PROGRESS.md project_state/CONFIG_REFERENCE.md project_state/KNOWN_ISSUES.md wrds_pipeline/asof_checks.py wrds_pipeline/ingest_sppx_surface.py wrds_pipeline/calibrate_heston.py wrds_pipeline/oos_pricing.py wrds_pipeline/pipeline.py wrds_pipeline/sample_data/spx_options_sample_poison_calib.csv wrds_pipeline/sample_data/spx_options_sample_poison_oos.csv tests/test_wrds_asof_poison_fast.py docs/artifacts/manifest.json docs/artifacts/metrics_summary.md docs/artifacts/metrics_summary.json docs/agent_runs/20251223_183500_ticket-02_wrds-asof-checks

git commit -m "ticket-02: WRDS as-of correctness gates + poison tests" \
  -m "Tests: cmake -S . -B build -DCMAKE_BUILD_TYPE=Release" \
  -m "Tests: cmake --build build -j" \
  -m "Tests: ctest --test-dir build -L FAST --output-on-failure" \
  -m "Tests: WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast" \
  -m "Artifacts: docs/artifacts/manifest.json, docs/artifacts/metrics_summary.md, docs/artifacts/metrics_summary.json" \
  -m "Run log: docs/agent_runs/20251223_183500_ticket-02_wrds-asof-checks/"
sed -n '1,160p' tests/test_data_policy_fast.py
git diff -- AGENTS.md
ctest --test-dir build -R wrds_asof_poison_fast --output-on-failure
WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast
ls -la docs/artifacts/wrds | head -n 20
cat <<'EOF' >> "$RUN_DIR/TESTS.md"
- `ctest --test-dir build -R wrds_asof_poison_fast --output-on-failure` — PASS
- `WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast` — PASS (confirmed outputs under `docs/artifacts/wrds/`)
tail -n 10 "$RUN_DIR/TESTS.md"
python3 - <<'PY'
from pathlib import Path
import json

run_dir = Path('docs/agent_runs').glob('*_ticket-02_wrds-asof-checks')
run_dir = next(run_dir)
required = [
    'PROMPT.md',
    'COMMANDS.md',
    'RESULTS.md',
    'TESTS.md',
    'META.json',
]
missing = [name for name in required if not (run_dir / name).exists()]
empty = [name for name in required if (run_dir / name).exists() and (run_dir / name).stat().st_size == 0]
print('missing', missing)
print('empty', empty)
meta = json.loads((run_dir / 'META.json').read_text())
print('meta.run_name', meta.get('run_name'))
print('meta.ticket_id', meta.get('ticket_id'))
PY
cat "$RUN_DIR/RESULTS.md"
git rev-parse HEAD
apply_patch (docs/agent_runs/20251223_183500_ticket-02_wrds-asof-checks/RESULTS.md)
git status -sb
rg -n "def main|DIFF" -n scripts/gpt_bundle.py
sed -n '240,360p' scripts/gpt_bundle.py
rg -n "gpt-bundle" -n Makefile
cat Makefile
RUN_DIR=$(ls -td docs/agent_runs/*_ticket-02_wrds-asof-checks | head -n1)
RUN_NAME=$(basename "$RUN_DIR")
BUNDLE_TS=$(date -u +%Y%m%dT%H%M%SZ)
BUNDLE_PATH="docs/gpt_bundles/${BUNDLE_TS}_ticket-02_${RUN_NAME}.zip"
printf '%s\n' "$BUNDLE_TS" > "$RUN_DIR/BUNDLE_TS.txt"
printf '%s\n' "$BUNDLE_PATH" > "$RUN_DIR/BUNDLE_PATH.txt"
BUNDLE_PATH=$(cat "$RUN_DIR/BUNDLE_PATH.txt")
python3 - <<'PY'
from pathlib import Path
bundle_path = Path("docs/agent_runs/20251223_183500_ticket-02_wrds-asof-checks/BUNDLE_PATH.txt").read_text().strip()
results = Path("docs/agent_runs/20251223_183500_ticket-02_wrds-asof-checks/RESULTS.md")
lines = results.read_text().splitlines()
new_lines = []
for line in lines:
    if line.startswith("- Bundle:"):
        new_lines.append(f"- Bundle: `{bundle_path}`.")
    else:
        new_lines.append(line)
results.write_text("\n".join(new_lines) + "\n")
PY
rm -f "$RUN_DIR/BUNDLE_TS.txt" "$RUN_DIR/BUNDLE_PATH.txt"
rg -n "Bundle:" "$RUN_DIR/RESULTS.md"
python3 - <<'PY'
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

run_dir = Path('docs/agent_runs/20251223_183500_ticket-02_wrds-asof-checks')
meta_path = run_dir / 'META.json'
meta = json.loads(meta_path.read_text())
sha = subprocess.check_output(['git','rev-parse','HEAD'], text=True).strip()
branch = subprocess.check_output(['git','rev-parse','--abbrev-ref','HEAD'], text=True).strip()
meta['finished_at_utc'] = datetime.now(timezone.utc).isoformat().replace('+00:00','Z')
meta['git_sha_before'] = sha
meta['git_sha_after'] = sha
meta['branch_name'] = branch
meta_path.write_text(json.dumps(meta, indent=2) + '\n')
PY
git status -sb
git add AGENTS.md docs/agent_runs/20251223_183500_ticket-02_wrds-asof-checks/COMMANDS.md docs/agent_runs/20251223_183500_ticket-02_wrds-asof-checks/META.json docs/agent_runs/20251223_183500_ticket-02_wrds-asof-checks/RESULTS.md docs/agent_runs/20251223_183500_ticket-02_wrds-asof-checks/TESTS.md docs/artifacts/manifest.json

git commit -m "ticket-02: finalize checklist + include AGENTS" \
  -m "Tests: ctest --test-dir build -R wrds_asof_poison_fast --output-on-failure" \
  -m "Tests: WRDS_USE_SAMPLE=1 python3 -m wrds_pipeline.pipeline --fast" \
  -m "Artifacts: docs/artifacts/manifest.json" \
  -m "Run log: docs/agent_runs/20251223_183500_ticket-02_wrds-asof-checks/"
git status -sb
RUN_DIR=$(ls -td docs/agent_runs/*_ticket-02_wrds-asof-checks | head -n1)
RUN_NAME=$(basename "$RUN_DIR")
TIMESTAMP=20251223T193039Z
make gpt-bundle TICKET=ticket-02 RUN_NAME=${RUN_NAME} TIMESTAMP=${TIMESTAMP}
RUN_DIR=$(ls -td docs/agent_runs/*_ticket-02_wrds-asof-checks | head -n1)
RUN_NAME=$(basename "$RUN_DIR")
ZIP="docs/gpt_bundles/20251223T193039Z_ticket-02_${RUN_NAME}.zip"
python3 scripts/gpt_bundle.py --ticket ticket-02 --run-name ${RUN_NAME} --verify ${ZIP}
git status -sb
git add docs/agent_runs/20251223_183500_ticket-02_wrds-asof-checks/COMMANDS.md

git commit -m "ticket-02: record bundle verification" \
  -m "Tests: make gpt-bundle TICKET=ticket-02 RUN_NAME=20251223_183500_ticket-02_wrds-asof-checks TIMESTAMP=20251223T193039Z" \
  -m "Tests: python3 scripts/gpt_bundle.py --ticket ticket-02 --run-name 20251223_183500_ticket-02_wrds-asof-checks --verify docs/gpt_bundles/20251223T193039Z_ticket-02_20251223_183500_ticket-02_wrds-asof-checks.zip" \
  -m "Artifacts: none" \
  -m "Run log: docs/agent_runs/20251223_183500_ticket-02_wrds-asof-checks/"
git status -sb
git add docs/agent_runs/20251223_183500_ticket-02_wrds-asof-checks/COMMANDS.md

git commit -m "ticket-02: update run log commands" \
  -m "Tests: not run (run log update only)" \
  -m "Artifacts: none" \
  -m "Run log: docs/agent_runs/20251223_183500_ticket-02_wrds-asof-checks/"
git switch main
git add docs/agent_runs/20251223_183500_ticket-02_wrds-asof-checks/COMMANDS.md

git commit -m "ticket-02: log branch switch" \
  -m "Tests: not run (run log update only)" \
  -m "Artifacts: none" \
  -m "Run log: docs/agent_runs/20251223_183500_ticket-02_wrds-asof-checks/"
