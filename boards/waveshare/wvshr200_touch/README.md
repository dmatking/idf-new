# Waveshare ESP32-S3 Touch LCD 2.0"

2.0" 240×320 IPS module from Waveshare. The ESP32-S3 module drives an ST7789 panel over SPI while a CST816S controller handles capacitive touch over I²C.

- **MCU:** ESP32-S3-WROOM-1
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

### CST816S Touch

| Signal | ESP32-S3 GPIO |
| ------ | ------------- |
| SDA    | IO48 |
| SCL    | IO47 |
| INT    | (not populated)
| RST    | (not populated)

## Notes

- The board implementation clocks the ST7789 at 40 MHz and flips the panel into color-invert mode to match the vendor LVGL demo.
- Touch I²C traffic runs on port 0 @ 400 kHz with address `0x15`. A lightweight FreeRTOS task logs touch coordinates to the console for quick bring-up.
- Adjust orientation via `esp_lcd_panel_mirror`/`esp_lcd_panel_swap_xy` in `board_impl.c` if your UI needs landscape mode.
