# ESP32-S3-DevKitC + Newhaven 2.4" IPS (ST7789 over i80)

[Goto Home](/README.md)

This board definition targets the official Espressif ESP32‑S3‑DevKitC wired to a Newhaven 2.4" 240x320 IPS TFT module (model family like NHD-2.4-240320AF-CSXP-CTP). The display uses an ST7789 controller over the 8080 (i80) 8‑bit parallel bus.

Notes
- Resolution: 240x320 (portrait by default)
- Technology: TFT IPS
- Controller: ST7789
- Interface: i80 8‑bit + CS/DC/WR, RDX held high
- Touch: The referenced Newhaven variant supports CTP, but touch is not wired here (set has_touch=false). Add an I2C touch driver later if used.

Wiring
- Data bus DB8–DB15 -> GPIOs 4,5,6,7,15,16,17,18 (in order)
- DC -> GPIO 10
- WR -> GPIO 11
- CS -> GPIO 9
- RST -> GPIO 12
- RD -> tied high externally

Build
- Requires ESP-IDF >= 5.1
- Component deps are declared in idf_component.yml

