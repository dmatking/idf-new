// Copyright 2025 David M. King
// SPDX-License-Identifier: Apache-2.0

#pragma once
#include "esp_err.h"

// Initialize the QMI8658 IMU over I2C (SCL=IO10, SDA=IO11).
// The I2C bus is shared with the RTC — call board_init() first.
esp_err_t imu_init(void);

typedef struct {
    float accel_x, accel_y, accel_z;   // m/s²
    float gyro_x,  gyro_y,  gyro_z;    // deg/s
} imu_data_t;

esp_err_t imu_read(imu_data_t *out);
