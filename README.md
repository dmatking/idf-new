# idf-new — ESP-IDF Project Generator

**idf-new** is a command-line tool that generates clean, minimal ESP-IDF projects for specific ESP32 boards. Projects can optionally include reusable hardware features like displays, GPS, and LVGL — without copy-pasting old repos or re-discovering pinouts.

```bash
idf-new my_project --board generic
```

That single command produces a ready-to-build ESP-IDF project wired correctly for the selected board and features.

The Generic ESP32 board target builds a minimal FreeRTOS-based project and should run on nearly any ESP32 supported by ESP-IDF. It’s intended as a quick smoke test to verify that a board powers up, flashes, and runs correctly.

---

## ⚡ Quick Start

```bash
git clone https://github.com/dmatking/idf-new.git
cd idf-new
pip install -e .
```

Generate a project:

```bash
idf-new my_project --board generic
cd my_project
idf.py set-target <esp32 | esp32s3 | esp32c3 | etc.>
idf.py build flash monitor
```

If you see serial output from your board, you’re up and running.

---

## ✅ Prerequisites

idf-new assumes a working ESP-IDF development environment.

You’ll need:

- **Python 3.11+**
- **ESP-IDF installed** and `idf.py` available in your shell  
  (tested with ESP-IDF **v5.5.1**)

Quick sanity check:

```bash
python --version
idf.py --version
```

If both commands work, you’re good.

> If `idf.py` is not found, install ESP-IDF using Espressif’s official installer or setup guide for your OS.

idf-new **does not install ESP-IDF for you** — it generates projects that ESP-IDF builds and flashes.

---

## 🚀 What This Tool Does

ESP-IDF users often accumulate a pile of boards, each slightly different:

- different pins  
- different LCDs  
- different SPI buses  
- different touch controllers  
- different UART wiring  

Setting up a new project for an existing board usually means:

- copy an old repo  
- fix board pins  
- rip out hacks  
- clean up unused code  
- add new features manually  
- hope it still builds  

idf-new replaces that workflow with a single command:

```bash
idf-new my_project --board generic --gps --lvgl
```

Every generated project contains **only the files it needs** — no bloat, no leftovers.

---

## 🧩 Core Concepts

idf-new is built around four simple ideas:

- **Boards** — Hardware-specific wiring and pin definitions  
- **Features** — Optional, reusable modules (GPS, LVGL, Wi-Fi, etc.)  
- **Templates** — A minimal ESP-IDF base project with no hardware assumptions  
- **Generator** — A Python CLI that assembles the above into a working project  

---

## 🧠 High-Level Architecture

```
idf-new/
├── boards/           # Board pinouts & wiring (per-board C files)
├── features/         # Reusable C modules (GPS, LVGL, WiFi, etc.)
├── idf-templates/    # Minimal ESP-IDF project template
└── idf_new_tool/     # Python-based project generator
```

### boards/
Each board implements functions declared in `board_interface.h` and defines all hardware wiring.

### features/
Optional feature modules (GPS, LVGL, WiFi, etc.).  
Only selected features are copied into generated projects.

### idf-templates/
A minimal ESP-IDF project:
- `main.c`
- board interface
- base `CMakeLists.txt`

Contains **no** board- or feature-specific code.

### idf_new_tool/
The Python generator:
- CLI (`idf-new`)
- project creation logic
- board discovery & validation
- feature plugin system
- template patching and file copying

---

## 🛠️ How Project Generation Works

Example:

```bash
idf-new myapp --board generic --gps --lvgl
```

This command:

1. Copies the base ESP-IDF template
2. Applies the selected board wiring
3. Applies selected features (GPS, LVGL)
4. Merges `Kconfig` snippets
5. Updates project names and paths

The result is a minimal, fully wired ESP-IDF project ready to build.

---

## 🔍 Discovering Boards and Features

To see what’s available:

```bash
idf-new --list-boards
idf-new --list-features
```

---

## 🧩 Adding a New Board

1. Create a new folder: `boards/<board_id>/`
2. Add:
   - `board_impl.c`
   - optional `idf_component.yml`
3. Implement required functions from `board_interface.h`
4. Generate a test project to verify everything builds and runs

---

## 🧩 Adding a New Feature

1. Create `features/<name>/` containing:
   - `<name>.c`
   - `<name>.h`
   - `Kconfig`
2. Add a Python module:
   ```
   idf_new_tool/idf_new/features/<name>.py
   ```
3. Register the feature in Python

You can now enable it via:

```bash
idf-new my_project --<name>
```

---

## 🔧 Installation Notes

Recommended (from repo root):

```bash
pip install -e .
```

Alternatively:

```bash
pip install -e ./idf_new_tool
```

During development, you may also run:

```bash
python -m idf_new_tool.idf_new.cli ...
```

---

## 💡 Why idf-new Exists

idf-new grew out of repeatedly solving the same ESP-IDF setup problems across many boards and projects.

Rather than maintaining dozens of near-duplicate repos, this tool centralizes:
- board knowledge
- feature modules
- clean project structure

The goal is to make starting a new ESP32 project **boring** — in the best possible way.

---

## 🔐 Licensing

All original code in this repository is licensed under the **Apache License 2.0**.

ESP-IDF and bundled third-party libraries are licensed separately under permissive licenses (Apache, MIT, BSD, etc.).

---

Built with:
- Python 3.13.5
- ESP-IDF 5.5.1

Enjoy building clean ESP-IDF projects 🚀

<center> This repository was automatically pushed from my self-hosted Forgejo server. Give it a try <a href="https://forgejo.org/">Forgejo</a>. </center>
