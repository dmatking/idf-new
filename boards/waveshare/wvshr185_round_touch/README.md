# Waveshare ESP32-S3 Round Touch LCD 1.85"

[Goto Home](/README.md)

Touch-enabled variant of the Waveshare ESP32-S3 round LCD kit. Ships with a CST816S capacitive touch controller bonded to the 1.85" ST77916 (360×360) panel.

Waveshare ESP32-S3 1.85" round with and without touch [Waveshare 1.85"](https://www.waveshare.com/product/arduino/boards-kits/esp32-s3/esp32-s3-touch-lcd-1.85.htm)

- **MCU:** ESP32-S3-WROOM-1
- **LCD:** ST77916 over QSPI (same routing as the non-touch board)
- **Touch:** CST816S over I²C with INT pin
- **Backlight:** PWM on GPIO5
- **Reset lines:** LCD and touch reset lines are driven through the onboard TCA9554 expander

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
| RST    | TCA9554 EXIO2 (no direct GPIO)
| BLK    | IO5 |

### CST816S Touch

| Signal | ESP32-S3 GPIO |
| ------ | ------------- |
| SDA    | IO1 |
| SCL    | IO3 |
| INT    | IO4 |
| RST    | (driven by the I/O expander)

## Notes

- The board implementation reads ST77916 register `0x04` at a low (3 MHz) SPI clock. If the returned ID matches `00 02 7F 7F`, the code uploads a vendor-specific init table before switching back to the normal 40 MHz QSPI clock. Panels reporting other IDs fall back to the default Espressif init sequence.
- Touch I²C traffic runs on port 0 @ 400 kHz with address `0x15`. A simple polling task logs coordinates for quick validation; hook your own driver if you need event routing.
- Reset lines for both LCD and touch continue to be driven through the on-board TCA9554 expander, so there is no dedicated ESP32 GPIO.
