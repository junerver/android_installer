# Repository Guidelines

## Project Structure & Module Organization
`main.py` is the GUI entry point, coordinating device polling, drag-and-drop APK installs, and UI state. `adb_utils.py` isolates all ADB calls, resolves the bundled `platform-tools/adb.exe`, and logs to `android_installer.log`. Packaging logic lives in `release.py`, which stages `platform-tools/` and creates PyInstaller bundles inside `dist/`. Treat `build/` and `dist/` as disposable artifacts, and reserve a future `tests/` package for automated coverage if added.

## Build, Test, and Development Commands
- `uv sync` - install dependencies declared in `pyproject.toml` into the managed virtual environment.
- `uv run python main.py` - launch the CustomTkinter desktop app and verify device status updates.
- `uv run python release.py` - assemble the distributable bundle and emit `dist/android_installer.zip` plus the extracted executable.
- `platform-tools/adb.exe devices` - confirm Windows recognizes connected Android hardware before attempting an install.

## Coding Style & Naming Conventions
Follow Python 3.13 conventions: four-space indenting, snake_case functions/modules, PascalCase classes, and UPPER_CASE constants such as `DeviceStatus`. Keep UI strings and comments in Chinese UTF-8 to match existing copy. Prefer structured logging through the module-level logger that writes to `android_installer.log`; avoid stray `print` calls. Co-locate helpers near related logic and include concise docstrings when intent is not obvious.

## Testing Guidelines
Automated suites are not yet defined, so prioritize manual verification. Exercise the full install loop with `uv run python main.py`, confirming the device list refreshes, status colors toggle, and sample APK installs without blocking the UI thread. Capture relevant excerpts from `android_installer.log` when reporting regressions. If you introduce tests, place them under `tests/test_<module>.py` and wire them into `uv run python -m pytest`.

## Commit & Pull Request Guidelines
Use Conventional Commits (e.g., `feat:`, `fix:`, `chore:`) in English or Chinese consistently. PR descriptions should summarize the change, list manual test steps, and attach screenshots or recordings for UI tweaks. Link related issues and flag any required changes to `platform-tools/` so reviewers can replicate your environment. Keep generated archives and executables out of version control.

## Security & Configuration Tips
Avoid modifying or replacing `platform-tools/` binaries unless explicitly coordinated, since the app relies on that portable SDK. Store sensitive device logs outside the repository when sharing builds, and rotate temporary APKs after testing to keep the workspace clean.
