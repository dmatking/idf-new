# Waveshare ESP32-S3 Round LCD 1.85" (Non-Touch)

[Goto Home](/README.md)

360 × 360 round LCD dev board from Waveshare. The panel is an ST77916 device wired over QSPI to the ESP32-S3-WROOM module, with a discrete LED backlight FET tied to GPIO5.

Waveshare ESP32-S3 1.85" round with and without touch [Waveshare 1.85"](https://www.waveshare.com/product/arduino/boards-kits/esp32-s3/esp32-s3-touch-lcd-1.85.htm)

- **MCU:** ESP32-S3-WROOM-1
- **LCD:** 1.85" 360×360 ST77916 (QSPI + TE)
- **Backlight:** LEDC PWM on GPIO5 (active high)
- **Reset:** Routed through the on-board TCA9554 expander (EXIO2)

## Pin Reference

### ST77916 QSPI Panel

| Signal | ESP32-S3 GPIO |
| ------ | ------------- |
| CLK    | IO40 |
| D0     | IO46 |
| D1     | IO45 |
| D2     | IO42 |
| D3     | IO41 |
| CS     | IO21 |
| TE     | IO18 |
| RST    | TCA9554 EXIO2 (not a native GPIO)
| BLK    | IO5 (LEDC low-speed channel 0)


> The board implementation uses Espressif's `esp_lcd_st77916` component with a 16-bit RGB565 frame buffer clocked at 40 MHz by default. Adjust `io_cfg.pclk_hz` inside `board_impl.c` if you need a slower or faster pixel clock.

## Notes

- The base `board_impl.c` already contains the minimal ST77916 bring-up for this kit, so no extra vendor sources are required.
- If you do not require the TE line, you can leave IO18 floating; it is only used for tearing sync.
- The board ships without a touch controller. Use the `wvshr_1.85_esp32s3_touch` target if you have the CST816-equipped version.
