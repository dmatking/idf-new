# idf-new – ESP-IDF Project Generator

**idf-new** is a modular project generator for ESP-IDF.  
It helps you quickly bootstrap working ESP32 projects across a large collection of ESP32 + display combo boards, without constantly digging through old repos to find pinouts, display configs, or boilerplate code.

This repo is designed to serve two purposes:

1. **A user-friendly tool** (`idf-new`) that generates clean ESP-IDF projects for specific boards with optional hardware feature modules (GPS, LVGL UI, WiFi helpers, etc.).  
2. **A knowledge base** of board-specific wiring, reusable feature modules, and a minimal ESP-IDF template that together eliminate repetitive setup work.

---

## 🚀 What This Tool Does

ESP-IDF users often have a *pile* of boards, each slightly different:

- different pins  
- different LCDs  
- different SPI buses  
- different touch controllers  
- different UART wiring  

Setting up each project becomes tedious:

- copy some old project  
- fix board pins  
- rip out old hacks  
- clean up unneeded code  
- add new features manually  
- hope it still builds  

**This tool solves that by letting you do:**

```bash
idf-new my_project --board generic --gps --lvgl
```

…and you instantly get a *clean*, *minimal*, *correctly-wired*, *feature-enabled* ESP-IDF project.

Every project contains only the files it needs. No bloat. 

---

## 🧠 High-Level Architecture

The system is made of four main pieces:

```
idf-new/
├── boards/           # Board pinouts & wiring (per-board C files)
├── features/         # Reusable C modules (GPS, LVGL, WiFi, etc.)
├── idf-templates/    # Minimal ESP-IDF project template
└── idf_new_tool/     # Python-based project generator
```

---

## 📦 Repository Structure (Explained)

### `boards/` – board-specific wiring implementations

Each board implements functions declared in `board_interface.h` and defines hardware wiring.

### `features/` – reusable feature modules (C code)

Features are optional modules (GPS, LVGL, WiFi, etc.).  
The generator copies only selected features into new projects.

### `idf-templates/` – minimal ESP-IDF base project

Provides `main.c`, board interface, and base CMakeLists.  
Contains no hardware or feature-specific code.

### `idf_new_tool/` – Python generator

Implements:

- CLI (`idf-new`)
- project creation logic
- feature plugin system
- board discovery & validation
- template patching + file copying

---

## 🛠️ How a Project Is Generated

Example:

```bash
idf-new myapp --board generic --gps --lvgl
```

This:

1. Copies the base project
2. Applies board wiring
3. Applies features (GPS, LVGL)
4. Merges Kconfig snippets
5. Updates project names
6. Produces a minimal, fully wired project

---

## 🧩 How to Add a New Board

1. Create a new folder in `boards/<board_id>/`
2. Add `board_impl.c` and optional `idf_component.yml`
3. Implement required functions from `board_interface.h`
4. Generate a test project to verify everything works

---

## 🧩 How to Add a New Feature

1. Create `features/<name>/` with:

```
<name>.c
<name>.h
Kconfig
```

2. Add a Python module under:

```
idf_new_tool/idf_new/features/<name>.py
```

3. Register the feature in Python

You can now use `--<name>` in the generator.

---

## 🔧 Installation & Usage - This has not been tested. dmk

```bash
cd idf_new_tool
pip install -e .
```

Then:

```bash
idf-new <project_name> --board <board_id> [--gps] [--lvgl]
```

*(Developing inside this repo? You can equivalently run `python -m idf_new_tool.idf_new.cli ...`.)*

---

## 🔐 Licensing

All original code in this repository is licensed under Apache License 2.0.  
ESP-IDF and its bundled third-party libraries are licensed separately under permissive licenses (Apache, MIT, BSD, etc.).

---

Enjoy building clean ESP-IDF projects! 🚀


#### Built using Python 3.13.5
#### ESP-IDF verion 5.5.1

## What has been completed:
 - Main CLI - invoke it from the repo root with `idf-new project_name --board generic` (or run `python -m idf_new_tool.idf_new.cli ...` during development)
 - Boards
    - Generic ESP32 - very simple test that should work for almost any ESP32. Creates a FreeRTOS task and outputs a count to the serial console. No other peripherals are initialized. [Generic ESP32](boards/generic/README.md)
    - `hackerbox/hb107_round128` — [HackerBox 107](boards/hackerbox/hb107_round128/README.md)
    - `lilygo/tdisp191_amoled_touch` — [LilyGO T-Display S3 AMOLED Touch](boards/lilygo/tdisp191_amoled_touch/README.md)
    - `waveshare/wvshr185_round` / `waveshare/wvshr185_round_touch` — [Waveshare 1.85" Round](boards/waveshare/wvshr185_round/README.md) and [Touch](boards/waveshare/wvshr185_round_touch/README.md)
    - `waveshare/wvshr200_touch` — [Waveshare ESP32-S3 2" 240×320 Touch](boards/waveshare/wvshr200_touch/README.md) ([product page](https://www.waveshare.com/product/arduino/boards-kits/esp32-s3/esp32-s3-touch-lcd-2.htm))


## Coming soon

 - Beginner's tutorial
 - Python installation improvements

  - Boards
     - Waveshare ESP32-P4 Smart 86 Box Development Board with 720x720 touch screen [ESP32-P4 Smart 86 Box](https://www.waveshare.com/product/arduino/boards-kits/esp32-p4/esp32-p4-wifi6-touch-lcd-4b.htm)
     - Official Espressif ESP32-P4-Function-EV-Board with 1024x600 touch screen [ESP32-P4-Function-EV-Board](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32p4/esp32-p4-function-ev-board/user_guide.html)
     - Official Espressif ESP32-S3-DevKitC-1 [ESP32-S3-DevKitC-1](https://docs.espressif.com/projects/esp-dev-kits/en/latest/esp32s3/esp32-s3-devkitc-1/user_guide_v1.1.html#getting-started)
     - Various Lilygo dev boards [Lilygo](https://lilygo.cc/)



<center> This repository was automatically pushed from my self-hosted Forgejo server. Give it a try <a href="https://forgejo.org/">Forgejo</a>. </center>
