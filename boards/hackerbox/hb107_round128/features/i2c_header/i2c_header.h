// Copyright 2025 David M. King
// SPDX-License-Identifier: Apache-2.0

#pragma once
#include "esp_err.h"

// Initialize I2C bus on the board's header pins (SDA=IO21, SCL=IO22).
// Port and speed are configured via menuconfig (CONFIG_I2C_HEADER_*).
esp_err_t i2c_header_init(void);
