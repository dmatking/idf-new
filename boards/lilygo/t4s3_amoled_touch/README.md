# LilyGO T4 S3 AMOLED Touch (2.41")

- Panel: RM690B0 (AMOLED)
- Resolution: 600x450 (landscape)
- Bus: QSPI over SPI3
- Touch: CST226 (I2C) — not yet integrated in this board_impl

## Pinout (from LilyGo product definitions)

- LCD CS: GPIO 11
- LCD SCK: GPIO 15
- LCD D0: GPIO 14
- LCD D1: GPIO 10
- LCD D2: GPIO 16
- LCD D3: GPIO 12
- LCD RST: GPIO 13
- LCD EN (power): GPIO 9
- LCD TE: not used

- I2C SDA (touch): GPIO 6
- I2C SCL (touch): GPIO 7
- Touch IRQ: GPIO 8
- Touch RST: GPIO 17

## Notes

- SPI clock set to 36 MHz (per LilyGo defaults).
- RM690B0 init sequence adapted from LilyGo reference and expressed as register writes.
- Color encoding uses standard RGB565 (no lane remap).
- Touch (CST226) support can be added later via `esp_lcd_touch` if available or a small driver shim.
