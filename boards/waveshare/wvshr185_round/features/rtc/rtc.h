// Copyright 2025 David M. King
// SPDX-License-Identifier: Apache-2.0

#pragma once
#include "esp_err.h"
#include <stdint.h>

// PCF85063 RTC over I2C (SCL=IO10, SDA=IO11, INT=IO9).
// Shared I2C bus with IMU — call board_init() first.

typedef struct {
    uint8_t seconds;    // 0–59
    uint8_t minutes;    // 0–59
    uint8_t hours;      // 0–23
    uint8_t day;        // 1–31
    uint8_t month;      // 1–12
    uint16_t year;      // e.g. 2025
} rtc_time_t;

esp_err_t rtc_clock_init(void);
esp_err_t rtc_get_time(rtc_time_t *out);
esp_err_t rtc_set_time(const rtc_time_t *t);
