# LilyGO T-Display S3 AMOLED Touch (1.91")

Minimal board support for LilyGO's 1.91" AMOLED Touch (RM67162) kit. The panel runs in QSPI mode at 75 MHz using the RM67162 command set and a CST816S controller provides capacitive touch over I2C.

- **MCU:** ESP32-S3R8-WROOM
- **LCD:** 1.91" 536x240 RM67162 AMOLED (QSPI, landscape)
- **Touch:** CST816S (I2C, INT only)
- **Power:** AMOLED enable FET on GPIO38

## Pin Reference

### RM67162 QSPI Panel

| Signal | ESP32-S3 GPIO |
| ------ | ------------- |
| SCLK   | IO47 |
| D0     | IO18 |
| D1     | IO7 |
| D2     | IO48 |
| D3     | IO5 |
| CS     | IO6 |
| RST    | IO17 |
| TE     | IO9 |
| EN/BLK | IO38 |

### CST816S Touch

| Signal | ESP32-S3 GPIO |
| ------ | ------------- |
| SDA    | IO3 |
| SCL    | IO2 |
| INT    | IO21 |
| RST    | (not routed)

## Notes

- The board implementation copies LilyGO's RM67162 init table and issues it over the SPI3 host using four data lines plus command/address phases. The TE pin is unused but exposed on IO9 if you need tearing sync.
- Touch is configured through `esp_lcd_touch_cst816s` on I2C port 0 @ 400 kHz. A background task logs coordinates so you can verify the panel without LVGL.
- The AMOLED enable pin (IO38) is driven high during `board_init()`. Pull it low if you need to power-cycle the panel.
- Display resolution is treated as 536 (X, long edge) by 240 (Y). If you prefer a portrait UI, adjust the window/coordinate helpers in `board_impl.c` accordingly.
- The driver remaps RGB565 data internally to compensate for LilyGO's QSPI wiring, so you can use standard RGB565 values without worrying about channel order.
