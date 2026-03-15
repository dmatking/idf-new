# Waveshare ESP32-S3 Round LCD 1.85" (Non-Touch)

[Goto Home](/README.md)

360 x 360 round LCD dev board from Waveshare. The panel is an ST77916 device wired over QSPI to the ESP32-S3-WROOM module, with a discrete LED backlight FET tied to GPIO5.

Waveshare ESP32-S3 1.85" round with and without touch [Waveshare 1.85"](https://www.waveshare.com/product/arduino/boards-kits/esp32-s3/esp32-s3-touch-lcd-1.85.htm)

- **MCU:** ESP32-S3-WROOM-1
- **LCD:** 1.85" 360x360 ST77916 (QSPI + TE)
- **Backlight:** LEDC PWM on GPIO5 (active high)
- **Reset:** Routed through the on-board TCA9554 expander (EXIO2)

## Pin Reference

### ST77916 QSPI Panel (360x360)

| Signal | GPIO |
| ------ | ---- |
| CLK    | IO40 |
| D0     | IO46 |
| D1     | IO45 |
| D2     | IO42 |
| D3     | IO41 |
| CS     | IO21 |
| TE     | IO18 |
| RST    | TCA9554 EXIO2 (not a native GPIO) |
| BLK    | IO5 (LEDC low-speed channel 0) |

### I2C Bus (I2C_NUM_0, 400 kHz, shared by IMU, RTC, IO expander)

| Signal | GPIO |
| ------ | ---- |
| SCL    | IO10 |
| SDA    | IO11 |

### IMU -- QMI8658 (I2C address 0x6B)

Accel + gyro, 6-axis. Uses shared I2C bus above.

### RTC -- PCF85063 (I2C address 0x51)

Uses shared I2C bus above. Interrupt on IO9 (active low, not currently used in driver).

### IO Expander -- TCA9554PWR (I2C address 0x20)

Uses shared I2C bus above. Holds SD D3/CS HIGH for native SDMMC mode. Also drives LCD RST via EXIO2.

### TF Card (SDMMC native 1-bit)

| Signal | GPIO |
| ------ | ---- |
| CLK    | IO14 |
| CMD    | IO17 |
| D0     | IO16 |

SD D3/CS held HIGH by TCA9554 IO expander.

### Speaker -- MAX98357A (I2S_NUM_1)

| Signal | GPIO |
| ------ | ---- |
| BCK    | IO48 |
| LRCK   | IO38 |
| DIN    | IO47 |

### Microphone -- MSM261S4030H0R (I2S_NUM_0)

| Signal | GPIO |
| ------ | ---- |
| BCK    | IO15 |
| WS     | IO2  |
| SD     | IO39 |
| EN     | IO12 (active high) |

### UART Header (UART_NUM_1, 115200 baud)

| Signal | GPIO |
| ------ | ---- |
| TX     | IO43 |
| RX     | IO44 |

## Notes

> The board implementation uses Espressif's `esp_lcd_st77916` component with a 16-bit RGB565 frame buffer clocked at 40 MHz by default. Adjust `io_cfg.pclk_hz` inside `board_impl.c` if you need a slower or faster pixel clock.

- The base `board_impl.c` already contains the minimal ST77916 bring-up for this kit, so no extra vendor sources are required.
- If you do not require the TE line, you can leave IO18 floating; it is only used for tearing sync.
- The board ships without a touch controller. Use the `waveshare/wvshr185_round_touch` target if you have the CST816-equipped version.

## Verified Working

- [x] LCD (ST77916 QSPI, 360x360)
- [x] IMU (QMI8658, accel + gyro)
- [x] RTC (PCF85063)
- [x] Speaker (MAX98357A I2S DAC)
- [x] Microphone (MSM261S4030H0R I2S)
- [x] UART header (TX=IO43, RX=IO44)
- [x] TF card (TCA9554PWR IO expander + SDMMC native 1-bit)
- [ ] I2C header (SCL=IO10, SDA=IO11, shared bus with IMU/RTC/IO expander)
