# Waveshare ESP32-S3 Touch LCD 2.0"

2.0" 240×320 IPS module from Waveshare. This variant drives an ST7789 panel over SPI and **does not include touch**. Use `waveshare/wvshr200_touch` for the CST816S touch-enabled version.

- **MCU:** ESP32-S3-WROOM-1
- **Memory:** 512KB SRAM, 384KB ROM, 8MB PSRAM (octal SPI), 16MB flash
- **LCD:** ST7789 SPI panel (240×320, RGB565)
- **Touch:** CST816S over I²C
- **Backlight:** MOSFET tied to GPIO1 (simple on/off)

## Pin Reference

### ST7789 SPI Panel

| Signal | ESP32-S3 GPIO |
| ------ | ------------- |
| SCLK   | IO39 |
| MOSI   | IO38 |
| MISO   | IO40 |
| DC     | IO42 |
| CS     | IO45 |
| RST    | (wired to PMIC, uncontrolled, so use SW reset)
| BLK    | IO1 |

## Notes

- The board implementation clocks the ST7789 at 20 MHz (for stability) and flips the panel into color-invert mode to match the vendor LVGL demo.
- Adjust orientation via `esp_lcd_panel_mirror`/`esp_lcd_panel_swap_xy` in `board_impl.c` if your UI needs landscape mode.
- PSRAM is octal SPI — use `CONFIG_SPIRAM_MODE_OCT=y` (quad mode will fail with "PSRAM chip is not connected").
