# Commands

```bash
ls
sed -n '1,200p' AGENTS.md
sed -n '1,200p' docs/DOCS_AND_LOGGING_SYSTEM.md
ls project_state
sed -n '1,120p' project_state/ARCHITECTURE.md
git rev-parse HEAD
git rev-parse --abbrev-ref HEAD
date -u +%Y-%m-%dT%H:%M:%SZ
date +%Y-%m-%dT%H:%M:%S
python3 -V
cmake --version | head -n 1
c++ --version | head -n 1
uname -a
rg --files
sed -n '1,200p' Makefile
sed -n '1,200p' README.md
sed -n '1,200p' tools/project_state_generate.py
sed -n '200,400p' tools/project_state_generate.py
sed -n '400,800p' tools/project_state_generate.py
python3 tools/project_state_generate.py
python3 - <<'PY'
import json
from pathlib import Path
p=Path('project_state/_generated/repo_inventory.json')
obj=json.loads(p.read_text())
print('files', len(obj['files']))
print('roles', obj['summary']['role_counts'])
PY
python3 - <<'PY'
import json
from pathlib import Path
obj=json.loads(Path('project_state/_generated/symbol_index.json').read_text())
print('python_files', len(obj['files']))
mods=list(obj['modules'].keys())
print('modules', len(mods))
print('sample', sorted(mods)[:10])
import itertools
counts=[(f, len(d['functions']), len(d['classes'])) for f,d in obj['files'].items()]
counts_sorted=sorted(counts, key=lambda x:(-x[1]-x[2], x[0]))
print('top', counts_sorted[:10])
PY
python3 - <<'PY'
import json
from pathlib import Path
obj=json.loads(Path('project_state/_generated/import_graph.json').read_text())
# print modules with most deps
nodes=obj['nodes']
items=[(k,len(v)) for k,v in nodes.items()]
for mod, cnt in sorted(items, key=lambda x:(-x[1], x[0]))[:10]:
    print(mod, cnt)
PY
sed -n '1,200p' wrds_pipeline/pipeline.py
sed -n '1,200p' src/main.cpp
rg -n "argparse|click|typer" scripts wrds_pipeline python tests tools
rg --files tests
sed -n '1,200p' PROGRESS.md
ls -1 docs/agent_runs | sort
sed -n '1,200p' docs/agent_runs/20251222_175224_ticket-07b_data-policy-guard-fix/RESULTS.md
sed -n '1,160p' docs/agent_runs/20251222_044808_ticket-07_data-policy-guard/RESULTS.md
sed -n '1,160p' docs/agent_runs/20251222_032810_ticket-06c_bundle-hardgate-tests/RESULTS.md
sed -n '1,160p' project_state/INDEX.md
sed -n '1,200p' project_state/MODULE_SUMMARIES.md
sed -n '1,200p' project_state/FUNCTION_INDEX.md
sed -n '1,200p' project_state/PIPELINE_FLOW.md
sed -n '1,200p' project_state/DATAFLOW.md
sed -n '1,200p' project_state/CURRENT_RESULTS.md
sed -n '1,200p' docs/artifacts/metrics_summary.md
sed -n '1,200p' project_state/KNOWN_ISSUES.md
sed -n '1,120p' "ROADMAP (1).md"
sed -n '1,120p' project_state/ROADMAP.md
sed -n '1,200p' project_state/CONFIG_REFERENCE.md
sed -n '1,160p' wrds_pipeline/dateset.yaml
head -n 5 wrds_pipeline/sample_data/spx_options_sample.csv
sed -n '1,200p' data/README.md
ls -1 docs/gpt_bundles | tail -n 5
ls docs/PLAN_OF_RECORD.md
ls experiments
ls -1 include/quant
python3 - <<'PY'
import json
from pathlib import Path
obj=json.loads(Path('project_state/_generated/symbol_index.json').read_text())
files=obj['files']
rows=[]
for path, data in files.items():
    module=data['module']
    func=len(data['functions'])
    cls=len(data['classes'])
    if path.startswith('python/'):
        tag='python'
    elif path.startswith('scripts/'):
        tag='script'
    elif path.startswith('tests/'):
        tag='test'
    elif path.startswith('wrds_pipeline/'):
        tag='wrds_pipeline'
    elif path.startswith('tools/'):
        tag='tool'
    else:
        tag='misc'
    rows.append((module, path, func, cls, tag))
rows.sort(key=lambda r: r[0])
print('| Module | Path | Functions | Classes | Tag |')
print('| --- | --- | --- | --- | --- |')
for module, path, func, cls, tag in rows:
    print(f'| {module} | `{path}` | {func} | {cls} | {tag} |')
PY
python3 - <<'PY'
import json
from pathlib import Path
obj=json.loads(Path('project_state/_generated/symbol_index.json').read_text())
files=obj['files']
# create sorted by module
items=sorted(files.items(), key=lambda x: x[1]['module'])
for path, data in items:
    module=data['module']
    print(f"### {module} (`{path}`)")
    funcs=data['functions']
    classes=data['classes']
    if funcs:
        print("- functions:")
        for f in funcs:
            sig=f.get('signature') or ''
            name=f['name']
            print(f"  - `{name}{sig}`")
    else:
        print("- functions: (none)")
    if classes:
        print("- classes:")
        for c in classes:
            print(f"  - `{c['name']}`")
    print()
PY
python3 - <<'PY'
import json
from pathlib import Path
obj=json.loads(Path('project_state/_generated/import_graph.json').read_text())
edges=[]
for mod, deps in obj['nodes'].items():
    if deps:
        edges.append((mod, deps))
for mod, deps in sorted(edges):
    print(f"- `{mod}` -> {', '.join(deps)}")
PY
python3 - <<'PY'
from pathlib import Path
text=Path('docs/artifacts/metrics_summary.md').read_text()
lines=text.splitlines()
# parse generated at, manifest sha, status overview table
generated=None
manifest_sha=None
status=[]
for line in lines:
    if line.startswith('Generated at:'):
        generated=line.split(':',1)[1].strip()
    if line.startswith('Manifest git sha:'):
        manifest_sha=line.split(':',1)[1].strip()
# parse status overview table
in_table=False
for i,line in enumerate(lines):
    if line.strip().startswith('| Block |'):
        in_table=True
        continue
    if in_table:
        if line.strip().startswith('| ---'):
            continue
        if not line.strip().startswith('|'):
            break
        parts=[p.strip() for p in line.strip().strip('|').split('|')]
        if len(parts)>=2:
            status.append((parts[0], parts[1], parts[2] if len(parts)>2 else ''))

print('generated', generated)
print('manifest', manifest_sha)
print('status', status)
PY
rg -n "artifacts/" scripts wrds_pipeline | head -n 40
sed -n '1,200p' CMakeLists.txt
sed -n '1,120p' requirements-dev.txt
sed -n '1,200p' requirements-artifacts.txt
sed -n '1,200p' scripts/reproduce_all.sh
sed -n '1,200p' python/pybind_module.cpp
git checkout -b chore/project_state_refresh
git checkout chore/project_state_refresh
git status -sb
git diff --stat
git diff --stat --cached
git status -sb -uall
git ls-files -m
git ls-files -v | rg '^h'
git ls-files -v | rg '^[S]'
git show chore/project_state_refresh:Makefile | sed -n '1,120p'
git checkout -b feature/ticket-00_project_state_refresh
rg --files -g '*.py'
date -u +%Y-%m-%dT%H:%M:%SZ
git rev-parse HEAD
git rev-parse --abbrev-ref HEAD
cat > project_state/INDEX.md <<'EOF'
# (content written; see file)
EOF
cat > project_state/ARCHITECTURE.md <<'EOF'
# (content written; see file)
EOF
cat > project_state/MODULE_SUMMARIES.md <<'EOF'
# (content written; see file)
EOF
cat > project_state/FUNCTION_INDEX.md <<'EOF'
# (content written; see file)
EOF
cat > project_state/DEPENDENCY_GRAPH.md <<'EOF'
# (content written; see file)
EOF
cat > project_state/PIPELINE_FLOW.md <<'EOF'
# (content written; see file)
EOF
cat > project_state/DATAFLOW.md <<'EOF'
# (content written; see file)
EOF
cat > project_state/EXPERIMENTS.md <<'EOF'
# (content written; see file)
EOF
cat > project_state/CURRENT_RESULTS.md <<'EOF'
# (content written; see file)
EOF
cat > project_state/RESEARCH_NOTES.md <<'EOF'
# (content written; see file)
EOF
cat > project_state/OPEN_QUESTIONS.md <<'EOF'
# (content written; see file)
EOF
cat > project_state/KNOWN_ISSUES.md <<'EOF'
# (content written; see file)
EOF
cat > project_state/ROADMAP.md <<'EOF'
# (content written; see file)
EOF
cat > project_state/CONFIG_REFERENCE.md <<'EOF'
# (content written; see file)
EOF
cat > project_state/SERVER_ENVIRONMENT.md <<'EOF'
# (content written; see file)
EOF
cat > project_state/TEST_COVERAGE.md <<'EOF'
# (content written; see file)
EOF
cat > project_state/STYLE_GUIDE.md <<'EOF'
# (content written; see file)
EOF
cat > project_state/CHANGELOG.md <<'EOF'
# (content written; see file)
EOF
python3 tools/project_state_generate.py
python3 - <<'PY'
from pathlib import Path
path=Path('CHANGELOG.md')
text=path.read_text()
entry="- docs(project_state): refresh project_state docs and generated indices"
if entry in text:
    print('Entry already present')
else:
    if '## Unreleased' in text:
        parts=text.split('## Unreleased')
        before=parts[0]
        after='## Unreleased'+parts[1]
        lines=after.splitlines()
        out=[]
        inserted=False
        for i,line in enumerate(lines):
            if line.startswith('## Unreleased'):
                out.append(line)
                continue
            if not inserted and line.startswith('## '):
                out.append(entry)
                inserted=True
            out.append(line)
        if not inserted:
            out.append(entry)
        text=before+'\n'.join(out)
    else:
        text=text.rstrip()+"\n\n## Unreleased\n"+entry+"\n"
    path.write_text(text)
PY
python3 tools/project_state_generate.py
sed -n '1,40p' CHANGELOG.md
python3 - <<'PY'
from pathlib import Path
path=Path('CHANGELOG.md')
lines=path.read_text().splitlines()
out=[]
for i,line in enumerate(lines):
    if line.strip()=='' and i>0 and lines[i-1].startswith('- wrds(local):') and i+1 < len(lines) and lines[i+1].startswith('- docs('):
        continue
    out.append(line)
path.write_text('\n'.join(out)+"\n")
PY
date +%Y%m%d_%H%M%S
mkdir -p docs/agent_runs/20251222_142116_ticket-00_project_state_rebuild
cat > docs/agent_runs/20251222_142116_ticket-00_project_state_rebuild/PROMPT.md <<'EOF'
# (content written; see file)
EOF
date +%Y-%m-%dT%H:%M:%S
cat > docs/agent_runs/20251222_142116_ticket-00_project_state_rebuild/META.json <<'EOF'
# (content written; see file)
EOF
cat > docs/agent_runs/20251222_142116_ticket-00_project_state_rebuild/RESULTS.md <<'EOF'
# (content written; see file)
EOF
cat > docs/agent_runs/20251222_142116_ticket-00_project_state_rebuild/TESTS.md <<'EOF'
# (content written; see file)
EOF
python3 tools/project_state_generate.py
date -u +%Y%m%dT%H%M%SZ
git rev-parse --short HEAD
zip -r docs/gpt_bundles/project_state_20251222T192333Z_5265c6d.zip project_state PROGRESS.md docs/PLAN_OF_RECORD.md docs/DOCS_AND_LOGGING_SYSTEM.md
python3 - <<'PY'
from pathlib import Path
path=Path('PROGRESS.md')
text=path.read_text()
old='docs/gpt_bundles/project_state_20251222T192333Z_5265c6d.zip'
new='docs/gpt_bundles/project_state_20251222T192635Z_5265c6d.zip'
if old in text:
    text=text.replace(old,new)
else:
    text=text.replace('project_state/_generated/*`). Produced bundle: `', f'project_state/_generated/*`). Produced bundle: `{new}`')
path.write_text(text)
PY
python3 - <<'PY'
from pathlib import Path
path=Path('docs/agent_runs/20251222_142116_ticket-00_project_state_rebuild/RESULTS.md')
text=path.read_text()
text=text.replace('docs/gpt_bundles/project_state_20251222T192333Z_5265c6d.zip','docs/gpt_bundles/project_state_20251222T192635Z_5265c6d.zip')
path.write_text(text)
PY
date -u +%Y%m%dT%H%M%SZ
zip -r docs/gpt_bundles/project_state_20251222T192635Z_5265c6d.zip project_state PROGRESS.md docs/PLAN_OF_RECORD.md docs/DOCS_AND_LOGGING_SYSTEM.md
tail -n 5 PROGRESS.md
rg -n "project_state_20251222T" docs/agent_runs/20251222_142116_ticket-00_project_state_rebuild/RESULTS.md
python3 tools/project_state_generate.py
python3 tools/project_state_generate.py
```
