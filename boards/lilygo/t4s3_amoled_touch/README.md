# LilyGO T4 S3 AMOLED Touch (2.41")

- Panel: RM690B0 (AMOLED, ~310 DPI)
- Resolution: 450 wide x 600 tall (portrait)
- Color: RGB565 (16-bit, byte-swapped on wire)
- Bus: QSPI over SPI3 at 36 MHz
- Touch: CST226 (I2C)
- PMU: SY6970 (battery charger, not required for display)

## Pinout

| Function    | GPIO |
|-------------|------|
| LCD CS      | 11   |
| LCD SCK     | 15   |
| LCD D0      | 14   |
| LCD D1      | 10   |
| LCD D2      | 16   |
| LCD D3      | 12   |
| LCD RST     | 13   |
| LCD EN      | 9    |
| I2C SDA     | 6    |
| I2C SCL     | 7    |
| Touch IRQ   | 8    |
| Touch RST   | 17   |

## Quick start

```bash
idf-new myproject --board lilygo/t4s3_amoled_touch
cd myproject
idf.py set-target esp32s3
idf.py build flash monitor
```

The generated project includes everything needed:
- `sdkconfig.defaults` — PSRAM (8MB OPI), 16MB flash, 240MHz CPU, USB JTAG console
- `components/XPowersLib` — vendored SY6970 PMU driver (no internet required)
- Display driver, touch driver, power driver, and init sequence

The sanity test cycles through red, green, blue, white, black fills.

## Board spec contents

```
boards/lilygo/t4s3_amoled_touch/
├── board_impl.c          # Display + board_interface shim
├── board.json            # Board metadata
├── sdkconfig.defaults    # ESP32-S3 hardware config (PSRAM, flash, etc.)
├── idf_component.yml     # IDF dependencies
├── main.cmake.extra      # Extra build config (compile defines, source files)
├── product_pins.h        # GPIO definitions
├── initSequence.c/h      # RM690B0 register init sequence
├── i2c_driver.c/h        # I2C bus for touch + PMU
├── power_driver.cpp/h    # SY6970 PMU driver
├── touch_min.c/h         # CST226 touch init
└── components/
    └── XPowersLib/       # Vendored PMU library
```

## Getting the display working

### Dimension gotcha

The vendor defines `AMOLED_WIDTH=600` and `AMOLED_HEIGHT=450`. These are
**swapped** relative to the physical panel orientation:

- `AMOLED_WIDTH` (600) = physical **height** (rows)
- `AMOLED_HEIGHT` (450) = physical **width** (columns)

When calling `display_push_colors(x, y, width, height, data)`, use:
- `width = amoled_height()` → 450 (physical columns)
- `height = amoled_width()` → 600 (physical rows)

The LVGL integration in the vendor code does this correctly:
`disp_drv.hor_res = AMOLED_HEIGHT`, `disp_drv.ver_res = AMOLED_WIDTH`.

### Column offset

The RM690B0 on this board requires a +16 pixel offset on x (column)
coordinates in `amoled_set_window`. This is already handled in the driver
code via `#if CONFIG_LILYGO_T4_S3_241`.

### Pixel push strategy

Row-by-row pushing does not produce visible output on this panel. The
working approach is a **full-frame push from PSRAM**:

```c
const int W = 450;  // amoled_height()
const int H = 600;  // amoled_width()
uint16_t *fb = heap_caps_malloc(W * H * sizeof(uint16_t),
                                MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT);
// ... fill fb ...
display_push_colors(0, 0, W, H, fb);
```

The framebuffer is ~527 KB, which fits comfortably in the 8 MB PSRAM.

### Color byte order

The ESP32 is little-endian but the display expects big-endian RGB565 on
the SPI wire. Byte-swap colors before writing:

```c
uint16_t swap16(uint16_t c) { return (c >> 8) | (c << 8); }

// Standard RGB565       Byte-swapped
// 0xF800 (red)     -->  0x00F8
// 0x07E0 (green)   -->  0xE007
// 0x001F (blue)    -->  0x1F00
```

### Coordinate system

- (0,0) is the top-left corner
- x increases rightward (0–449)
- y increases downward (0–599)
- This matches the orientation shown in LilyGo's product photos

### What's NOT needed for display

- I2C bus init (only needed for touch and PMU)
- SY6970 PMU init (display powers on without it)
- LVGL (the raw driver works standalone)
