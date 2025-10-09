# Repository Guidelines

## Project Structure & Module Organization
All runtime code now resides under `src/`. Use `src/main.py` as the GUI entry point for device polling, drag-and-drop installs, and UI state. Shared ADB helpers live in `src/adb_utils.py`, resolving the portable `platform-tools/adb.exe` and logging to `android_installer.log` at the repository root. Release automation moved to `script/release.py`; it bundles `src/`, flattens PyInstaller output, and stages `platform-tools/`. Treat `build/` and `dist/` as disposable artifacts, and reserve `tests/` for future automated coverage.

## Build, Test, and Development Commands
- `uv sync` - install dependencies declared in `pyproject.toml` into the managed environment.
- `uv run python src/main.py` - launch the CustomTkinter desktop app and verify device status updates.
- `uv run python script/release.py` - build the distributable bundle, yielding `dist/android_installer.zip` and the extracted executable.
- `platform-tools/adb.exe devices` - confirm Windows detects connected Android hardware before attempting an install.

## Coding Style & Naming Conventions
Follow Python 3.13 conventions: four-space indentation, snake_case for functions and modules, PascalCase for classes, and UPPER_CASE constants like `DeviceStatus`. Keep UI strings and comments in Chinese UTF-8 to match existing copy. Rely on the shared logger that writes to `android_installer.log`; avoid ad-hoc `print` calls. Place new helpers next to related logic within `src/`, and add concise docstrings when behavior is not obvious.

## Testing Guidelines
Automated suites remain pending, so emphasize manual verification. Run `uv run python src/main.py` to check device discovery, status color transitions, and sample APK installs without freezing the UI thread. Capture relevant snippets from `android_installer.log` when raising issues. House any future pytest suites under `tests/test_<module>.py` and execute them with `uv run python -m pytest`.

## Commit & Pull Request Guidelines
Adopt Conventional Commits (e.g., `feat:`, `fix:`, `chore:`) consistently in English or Chinese. Pull requests should summarize the change, document manual test steps, and attach screenshots or recordings for UI tweaks. Link associated issues and flag any updates to `platform-tools/` so reviewers can replicate. Keep generated archives and executables out of version control.

## Security & Configuration Tips
Avoid swapping the bundled `platform-tools/` binaries without coordination, since the app depends on that portable SDK. When sharing builds, relocate sensitive device logs outside the repo and clear temporary APKs after testing.
