# Repository Guidelines

## Project Structure & Module Organization
- `gamesdb/` holds the core package; `__init__.py` reads `gamesdb/data/config/config.yaml` and exposes `TARGET_DIR`, `OUTPUT_DIR`, and `DATASETS_DIR`.
- `gamesdb/data/config/` keeps shared YAML config files; adjust paths here whenever local directories change.
- `gamesdb/shellscripts/` contains operational helpers (e.g., `connect_to_rg34xx_sp.sh`, `create_backup.sh`) that wrap device-specific workflows.
- `gamesdb_tests/tests.py` provides repository-wide integration tests; mirror its patterns when adding new behaviors.
- `gamesdb_localdata/` is your scratch space for ROMs, covers, and generated datasets (ignored by git but required at runtime).

## Build, Test, and Development Commands
- `uv sync` installs locked dependencies defined in `uv.lock` and `pyproject.toml`.
- `uv run pytest gamesdb_tests` executes the Rich-enhanced integration suite and reports failures with styled panels.
- `uv run python -c "from gamesdb import TARGET_DIR, OUTPUT_DIR; from gamesdb.get_paths import get_paths; get_paths(TARGET_DIR, OUTPUT_DIR / 'paths.txt')"` regenerates the path index.
- `uv run python -c "from gamesdb import DATASETS_DIR, TARGET_DIR; from gamesdb.tree_to_csv_datasets import export_dataset; [export_dataset(DATASETS_DIR, d) for d in TARGET_DIR.iterdir() if d.is_dir()]"` refreshes dataset CSVs.

## Coding Style & Naming Conventions
- Target Python 3.13, with 4-space indentation, type hints, and `pathlib.Path` for filesystem access.
- Prefer f-strings and Rich panels/console output for user-facing messaging; keep emoji usage consistent with existing scripts.
- Name modules and test files with snake_case; functions should be verbs or verb phrases (`export_dataset`, `get_paths`).

## Testing Guidelines
- Use `pytest` fixtures (e.g., `tmp_path`) to isolate filesystem interactions; mimic the assertions in `gamesdb_tests/tests.py`.
- New tests should live in `gamesdb_tests/` and start with `test_`; cover both happy paths and error messaging.
- Aim to exercise Rich output paths minimally—assert artifacts instead of console text unless formatting is critical.

## Commit & Pull Request Guidelines
- Follow the existing short, imperative commit style (`tagging is good`, `pytest and uv management and refactoring.`); keep subjects under 72 characters.
- Each PR should describe the change, list manual test commands, and link issues or tasks; include screenshots or console captures when output changes.
- Update `gamesdb/data/config/config.yaml` in the same PR whenever directory semantics shift, and call this out explicitly in the description.

## Configuration Notes
- Ensure `gamesdb/data/config/config.yaml` points to valid absolute paths before running scripts; the package resolves them at import time.
- Populate `gamesdb_localdata/games_to_include/` with per-game subdirectories containing ROM and cover assets to enable dataset export pipelines.
