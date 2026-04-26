# esp32-idf-new — ESP-IDF Project Generator

**idf-new** is a command-line tool that generates clean, minimal ESP-IDF projects for specific ESP32 boards. Pick a board, pick optional peripherals and modules, and get a ready-to-build project — without copy-pasting old repos or re-discovering pinouts.

```bash
idf-new my_project --board waveshare/wvshr200_touch --feature tf_card --module gps_neo6m
```

---

## Quick Start

```bash
git clone https://github.com/dmatking/esp32-idf-new.git
cd esp32-idf-new
python3 -m venv .venv
source .venv/bin/activate
pip install -e idf_new_tool
```

> The `-e` (editable) flag is required — idf-new reads `boards/`, `modules/`, and `idf-templates/` directly from the repo checkout at runtime.

After the initial setup, activate the venv at the start of each session alongside ESP-IDF:

```bash
source ~/esp/esp-idf/export.sh
source ~/esp32-idf-new/.venv/bin/activate
```

> On Debian/Raspberry Pi OS, system Python is externally managed and blocks global pip installs. A venv sidesteps this cleanly. If you'd prefer a one-liner without a venv, see [Alternative: system-wide install](#alternative-system-wide-install).

Generate a project:

```bash
idf-new my_project --board generic
cd my_project
idf.py set-target <esp32 | esp32s3 | esp32c3 | etc.>
idf.py build flash monitor
```

If you see serial output from your board, you're up and running.

The `generic` board target builds a minimal FreeRTOS heartbeat project and should run on nearly any ESP32. It's a good smoke test to verify a board powers up, flashes, and runs correctly.

---

## Prerequisites

idf-new assumes a working ESP-IDF development environment.

You'll need:

- **Python 3.11+**
- **ESP-IDF installed** and `idf.py` available in your shell
  (tested with ESP-IDF **v5.5.1**)

Quick sanity check:

```bash
python --version
idf.py --version
```

> If `idf.py` is not found, install ESP-IDF using Espressif's official installer or setup guide for your OS.

idf-new **does not install ESP-IDF for you** — it generates projects that ESP-IDF builds and flashes.

---

## Core Concepts

idf-new is built around three tiers:

**1. Boards** — Hardware-specific wiring, pin definitions, LCD/touch initialization, and display drawing primitives. Every board implements a small C interface (`board_interface.h`).

**2. Board Features** — Optional peripherals that are physically on the board (TF card slot, speaker, buttons, etc.). These are board-specific — a feature only exists if the board has that hardware.

**3. Modules** — Generic off-the-shelf breakout boards you wire up yourself (GPS, sensors, IMUs, etc.). Modules use `menuconfig` for pin selection and work across any board.

Plus the base **Template** — a minimal ESP-IDF project with no hardware assumptions that everything is built on top of.

---

## High-Level Architecture

```
idf-new/
├── boards/           # Board wiring & pin definitions (per-board C files)
│   └── <vendor>/
│       └── <board>/
│           ├── board_impl.c       # Required: implements board_interface.h
│           ├── board.json         # Metadata for CLI listing
│           ├── idf_component.yml  # Component dependencies
│           ├── main.cmake.extra   # Optional CMake additions
│           └── features/          # Optional on-board peripherals
│               └── <name>/        # e.g. tf_card/, speaker/, buttons/
├── modules/          # Generic breakout board drivers
│   └── gps/
│       ├── _common/  # Shared NMEA/UART core (gps.c, gps.h, Kconfig)
│       ├── neo6m/    # u-blox NEO-6M / GY-NEO6MV2
│       └── atgm336h/ # ATGM336H
├── idf-templates/    # Minimal ESP-IDF base project template
└── idf_new_tool/     # Python CLI and generator
```

---

## How Project Generation Works

```bash
idf-new myapp --board waveshare/wvshr200_touch --feature tf_card --module gps_neo6m
```

This command:

1. Copies the base ESP-IDF template
2. Installs the selected board's wiring (`board_impl.c`, helpers, component deps)
3. Applies selected board features (copies `boards/.../features/tf_card/` into the project)
4. Applies selected modules (copies `modules/gps/_common/gps.c`, `gps.h`, merges `Kconfig`)
5. Merges all `idf_component.yml` dependency declarations
6. Updates project name and CMake config

The result is a minimal, fully wired ESP-IDF project ready to build.

---

## Discovering What's Available

```bash
idf-new --list-boards     # All supported boards
idf-new --list-modules    # All generic modules (GPS, sensors, etc.)
```

Board features are board-specific — check `boards/<vendor>/<board>/features/` or the board's `board.json` for what a given board supports.

---

## Adding a New Board

1. Create `boards/<vendor>/<board_name>/`
2. Add `board_impl.c` implementing the functions from `board_interface.h`:
   - **Required:** `board_init()`, `board_get_name()`, `board_has_lcd()`
   - **LCD boards:** `board_lcd_sanity_test()`, `board_lcd_fill()`, plus the display drawing API (`board_lcd_width()`, `board_lcd_height()`, `board_lcd_flush()`, `board_lcd_clear()`, `board_lcd_set_pixel_raw()`, `board_lcd_set_pixel_rgb()`, `board_lcd_pack_rgb()`, `board_lcd_get_pixel_raw()`, `board_lcd_unpack_rgb()`)
   - Weak no-op defaults are provided in `board_defaults.c` for headless boards
3. Optionally add:
   - `board.json` — metadata for `--list-boards`
   - `idf_component.yml` — component dependencies
   - `main.cmake.extra` — CMake additions (extra sources, defines, requires)
   - Additional `.c`/`.h` helper files (copied into generated project automatically)
   - `features/<name>/` — optional on-board peripheral implementations
4. Test: `idf-new test_proj --board <vendor>/<board_name>`

---

## Adding a Board Feature

Board features live under `boards/<vendor>/<board>/features/<name>/` and represent optional peripherals physically on that board (TF card, speaker, buttons, etc.).

1. Create `boards/<vendor>/<board>/features/<name>/`
2. Add any combination of:
   - `.c` / `.h` source files (copied into generated project's `main/`)
   - `Kconfig` — appended to `Kconfig.projbuild`
   - `idf_component.yml` — merged into project dependencies
   - `main.cmake.extra` — appended to project's CMake extras
3. Add `"board_features": ["<name>"]` to the board's `board.json`

Enable via:

```bash
idf-new my_project --board <vendor>/<board> --feature <name>
```

The `--feature` flag is repeatable: `--feature tf_card --feature buttons`

---

## Adding a New Module

Modules are generic drivers for off-the-shelf breakout boards. Pins are configured via `menuconfig`.

1. Create `modules/<category>/<module_name>/` with a `module.json` descriptor
2. Add shared C code under `modules/<category>/_common/` (or directly in the module dir)
3. Add a `Kconfig` with pin and configuration options
4. Create `idf_new_tool/idf_new/modules/<category>.py`:
   - Implement the `Module` protocol (`name`, `flag`, `category`, `apply()`)
   - Call `register()` at module load
   - `apply()` copies source files and merges Kconfig into the project

Enable via:

```bash
idf-new my_project --board generic --module <flag>
```

Use `idf-new --list-modules` to see registered modules.

---

## Desktop Simulator (`--sim`)

For boards with an LCD, `--sim` adds a native desktop build that renders your display code in an SDL2 window — no hardware needed. It can also save PNG screenshots for documentation.

```bash
idf-new my_project --board waveshare/wvshr_p4_720_touch --sim
```

This creates a `sim/` directory inside the generated project:

```
my_project/
├── main/             # Your ESP-IDF app code (runs on device)
└── sim/
    ├── CMakeLists.txt
    ├── main_sim.c    # Desktop entry point (replace gradient with your rendering)
    └── screencap/    # git submodule — esp32-screencap library
```

The sim compiles your project's `main/` drawing code (via `board_interface.h`) against a native SDL2 backend instead of real hardware. Your rendering code runs unchanged.

### Building and running

```bash
cd my_project/sim
mkdir build && cd build
cmake .. && make
./my_project_sim                                  # interactive SDL2 window
./my_project_sim --screenshot out.png --frames 1  # headless PNG capture
```

**Prerequisites:** `libsdl2-dev` (Debian/Ubuntu: `sudo apt install libsdl2-dev`)

### Interactive mode

- Live SDL2 window with integer-scaled preview
- Press **P** to save a screenshot (`screenshot_NNNN.png`)
- **Esc** or close the window to quit

### Headless mode

Works over SSH with no display server — useful for CI or headless Pis:

```bash
./my_project_sim --screenshot summary.png --frames 1
```

`--frames N` runs N iterations of your render loop before saving. This lets you capture specific screens if your app cycles through multiple views.

### How it works

The sim reuses your project's rendering code through `board_interface.h` — the same HAL that idf-new scaffolds for every LCD board. A generic `board_interface_sim.c` (provided by esp32-screencap) implements the HAL against an in-memory framebuffer. SDL2 displays it on screen; `stb_image_write` saves it as PNG.

Your drawing code doesn't know or care whether it's running on an ESP32 or a desktop — it just calls `board_lcd_set_pixel_rgb()`, `board_lcd_flush()`, etc.

### X11 forwarding

To view the SDL2 window from a remote Pi on your local machine:

```bash
ssh -X user@pi
cd my_project/sim/build && ./my_project_sim
```

On Windows, WSL2 with WSLg handles X11 forwarding natively — just `ssh -X` from a WSL terminal.

---

## Installation Notes

idf-new must be installed as an editable install from the repo checkout — it reads `boards/`, `modules/`, and `idf-templates/` from the repo at runtime.

```bash
git clone https://github.com/dmatking/esp32-idf-new.git
cd esp32-idf-new
python3 -m venv .venv
source .venv/bin/activate
pip install -e idf_new_tool
```

**To update:** just `git pull` in the repo — no reinstall needed.

---

## Using as an idf.py Extension (ESP-IDF v6.0+)

ESP-IDF v6.0 supports Python package entry-point extensions that add subcommands directly to `idf.py`. idf-new ships one — install it into the v6.0 Python venv and the `idfnew-*` commands appear alongside `build`, `flash`, and `monitor`.

### Install

Install idf-new into the v6.0 venv (find the venv path with `eim run "python -c 'import sys; print(sys.prefix)'" v6.0`):

```bash
/home/$USER/.espressif/tools/python/v6.0/venv/bin/pip install -e /path/to/esp32-idf-new
```

The editable install means updates from `git pull` take effect immediately — no reinstall needed.

### Verify

```bash
eim run "idf.py --help" v6.0  # idfnew-* commands should appear in the list
```

Or after activating the v6.0 environment:

```bash
. ~/.espressif/tools/activate_idf_v6.0.sh
idf.py --help
```

### Available commands

```bash
# List all boards, optionally filtered by tag
idf.py idfnew-boards
idf.py idfnew-boards --find touch

# Find boards by tag (shorthand)
idf.py idfnew-find --tag amoled

# List available modules grouped by category
idf.py idfnew-modules

# Generate a new project
idf.py idfnew-create --name myapp --board m5stack/tab5
idf.py idfnew-create --name myapp --board waveshare/wvshr200_touch --feature tf_card
idf.py idfnew-create --name myapp --board generic --dest ~/projects/myapp --gps_neo6m
```

> **Note:** `idfnew-create` uses named options only — there is no positional argument for the project name. idf.py's command chaining (click `chain=True`) interprets anything after a positional argument as the next chained command, so `--name` is used instead.

### After generating

The generated project is a standard ESP-IDF project. Continue using `idf.py` as normal:

```bash
cd myapp
idf.py set-target esp32s3
idf.py build flash monitor
```

### Standalone CLI

The standard `idf-new` command-line tool remains available alongside the extension:

```bash
idf-new --list-boards
idf-new myapp --board m5stack/tab5
```

---

## Alternative: system-wide install

If you don't want to manage a venv, you can install directly into your user Python environment. On Debian/Raspberry Pi OS you'll need to pass `--break-system-packages`:

```bash
pip install -e idf_new_tool --break-system-packages
```

This is safe for a dev tool with a single dependency (PyYAML), but the venv approach above is cleaner and won't interfere with system packages.

---

## Why idf-new Exists

idf-new grew out of repeatedly solving the same ESP-IDF setup problems across many boards and projects.

Rather than maintaining dozens of near-duplicate repos, this tool centralizes:

- board wiring knowledge
- optional peripheral implementations
- generic driver modules
- clean project structure

The goal is to make starting a new ESP32 project **boring** — in the best possible way.

---

## Licensing

All original code in this repository is licensed under the **Apache License 2.0**.

ESP-IDF and bundled third-party libraries are licensed separately under permissive licenses (Apache, MIT, BSD, etc.).
