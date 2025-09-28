# Repository Guidelines

## Project Structure & Module Organization
The GUI entry point lives in `main.py`, orchestrating device polling, drag-and-drop installation, and UI state management. ADB interactions are isolated in `adb_utils.py`, which resolves a portable `adb.exe`, wraps device status checks, and writes to `android_installer.log`. Packaging automation sits in `release.py`, copying `platform-tools/` and assembling the PyInstaller bundle. Generated artifacts land in `build/` and `dist/`; keep them out of version control. The bundled Android SDK tools remain under `platform-tools/`, so adjustments to the binary set should happen there.

## Build, Test, and Development Commands
Use `uv` for environment management: `uv sync` installs dependencies declared in `pyproject.toml`. Launch the desktop app with `uv run python main.py`, which spawns the CustomTkinter GUI. For a distributable build, run `uv run python release.py`; the resulting `android_installer.zip` and extracted executable appear in `dist/`. When debugging ADB connectivity, `uv run python -m adb_utils` is not provided; invoke `platform-tools/adb.exe devices` directly to verify device visibility.

## Coding Style & Naming Conventions
Follow standard Python 3.13 style: four-space indentation, snake_case for functions and modules, PascalCase for classes, and UPPER_CASE for constants like `DeviceStatus`. Keep UI copy and comments in UTF-8; existing strings are Chinese, so maintain locale consistency unless product direction changes. Prefer explicit logging via the shared `android_installer.log` handler instead of `print`. Structure new helpers near related logic and include docstrings when behavior is non-obvious.

## Testing Guidelines
Automated tests are not yet defined; prioritize manual verification. Before opening a pull request, confirm `uv run python main.py` detects devices, toggles status colors, and installs a sample APK without freezing the UI. Capture log excerpts from `android_installer.log` for regressions. If you introduce unit tests, place them under a new `tests/` package and name files `test_<module>.py` to align with pytest conventions anticipated here.

## Commit & Pull Request Guidelines
Commits follow Conventional Commits (e.g., `feat:`, `refactor:`, `chore:`) as seen in history, so continue that format and keep messages in English or Chinese consistently. Each pull request should summarize the change, note manual test steps, and attach screenshots or screen recordings when UI updates occur. Link related issues and call out any required ADB or platform-tool changes so reviewers can validate on their machines.
