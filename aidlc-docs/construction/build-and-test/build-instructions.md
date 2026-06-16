# Build Instructions — hbc-sync

## Prerequisites
- **Runtime**: Python 3.10+ (verified with 3.14.4)
- **Dependencies**: `pyyaml` (graph parsing), `hypothesis` (PBT tests, dev only)
- **Host**: BMad Method v6.3.0+ with BMM module; skills install to `.claude/skills/`
- **System**: Any OS with Python; no compilation, no cloud resources

## Build Steps

hbc-sync là skill module (không compile). "Build" = cài dependencies + verify scripts chạy.

### 1. Install Dependencies
```bash
python -m pip install pyyaml hypothesis
```
(pyyaml là runtime cho graph parsing; hypothesis chỉ cho dev/test.)

### 2. Verify Scripts Load
```bash
python src/hbc-sync/scripts/load-graph.py --graph src/hbc-sync/assets/dependency-graph.yaml --project-root .
```
- **Expected**: JSON với `"validation": {"valid": true, "is_dag": true}` và `topological_order` 11 node.

### 3. Install Skill (via BMad)

Cách an toàn — installer tương tác (giữ nguyên các module đang cài, vd `core`/`bmm`):
```bash
npx bmad-method install
```
Non-interactive **phải** liệt kê `--modules` để không gỡ module khác (chạy `--custom-source` đơn lẻ sẽ chỉ giữ `core` + module custom):
```bash
npx bmad-method install --directory . --modules bmm,bmb --custom-source <git-url> --tools claude-code --yes
```
Skill cài vào `.claude/skills/hbc-*/`.

## Build Artifacts
- `src/hbc-sync/SKILL.md`, `customize.toml`
- `src/hbc-sync/assets/dependency-graph.yaml`
- `src/hbc-sync/scripts/*.py` (load-graph, analyze-impact, sync-state, sync_common)
- `src/hbc-sync/references/*.md`

## Troubleshooting

### `PyYAML not installed` (exit code 2)
- **Cause**: pyyaml missing
- **Solution**: `python -m pip install pyyaml`

### `graph_has_cycle` / validation invalid
- **Cause**: dependency-graph.yaml có cycle hoặc dangling edge
- **Solution**: kiểm tra `depends_on`, đảm bảo mọi parent tồn tại và không tạo vòng
