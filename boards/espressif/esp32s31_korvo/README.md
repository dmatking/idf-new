# Espressif ESP32-S31-Korvo

Espressif's ESP32-S31-Korvo development board featuring a 4.3" 800×480 RGB parallel LCD with GT1151 touch, a DVP camera connector, audio codec, and microSD slot.

| Detail      | Value                                        |
| ----------- | -------------------------------------------- |
| MCU         | ESP32-S31 (dual-core Xtensa LX8)             |
| Display     | 4.3" IPS 800×480, 16-bit RGB parallel        |
| Touch       | GT1151 capacitive (I2C, SDA=GPIO0, SCL=GPIO1)|
| Camera      | DVP 8-bit (OV3660 or compatible)             |
| Audio       | ES8389 codec (I2S + I2C)                     |
| SD card     | SDMMC 4-bit on GPIO20–25, control GPIO39     |
| LED         | WS2812 RGB on GPIO37                         |
| Buttons     | 4 × ADC ladder on GPIO42                     |
| PSRAM       | 250 MHz                                      |
| Flash       | 16 MB                                        |
| Backlight   | NC (always on)                               |

**Requires IDF 6.1** — the `esp32s31` target (specifically `components/soc/esp32s31`) is only present in
the `release/v6.1` branch. IDF 6.1.0 has not been officially released yet; use the branch directly:

```powershell
# Install the release/v6.1 branch via eim (or clone manually)
. "C:\Espressif\tools\Microsoft.v6.1.PowerShell_profile.ps1"
$env:PYTHONIOENCODING = "utf-8"
```

## Build

```powershell
idf-new my_project --board espressif/esp32s31_korvo
cd my_project
idf.py build
idf.py flash
```

## Notes

- The RGB panel has no backlight or DISP_EN GPIO; the display is always on once powered.
- Touch is optional: `board_init()` logs a warning and continues if the GT1151 is not detected.
- `board_lcd_flush()` uses `esp_cache_msync` to push CPU cache lines to PSRAM; the RGB DMA
  controller continuously scans the framebuffer without further CPU intervention.
