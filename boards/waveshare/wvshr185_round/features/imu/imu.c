// Copyright 2025-2026 David M. King
// SPDX-License-Identifier: Apache-2.0

// QMI8658 6-axis IMU over I2C
// I2C bus: SCL=IO10, SDA=IO11 (shared with RTC and IO expander)
// I2C address: 0x6B (SA0 high) or 0x6A (SA0 low)

#include "imu.h"
#include "driver/i2c.h"
#include "esp_log.h"

static const char *TAG = "IMU";

#define I2C_PORT        CONFIG_IMU_I2C_PORT
#define I2C_PIN_SCL     10
#define I2C_PIN_SDA     11
#define IMU_ADDR        0x6B

// QMI8658 register map (subset)
#define REG_WHO_AM_I    0x00
#define REG_CTRL1       0x02    // SPI/I2C config
#define REG_CTRL2       0x03    // accel config
#define REG_CTRL3       0x04    // gyro config
#define REG_CTRL7       0x08    // enable sensors
#define REG_ACCEL_X_L   0x35
#define REG_GYRO_X_L    0x3B

#define QMI8658_WHO_AM_I 0x05

static esp_err_t i2c_write_reg(uint8_t reg, uint8_t val)
{
    uint8_t buf[2] = {reg, val};
    return i2c_master_write_to_device(I2C_PORT, IMU_ADDR, buf, sizeof(buf), pdMS_TO_TICKS(50));
}

static esp_err_t i2c_read_regs(uint8_t reg, uint8_t *data, size_t len)
{
    return i2c_master_write_read_device(I2C_PORT, IMU_ADDR, &reg, 1, data, len, pdMS_TO_TICKS(50));
}

static esp_err_t init_i2c_bus(void)
{
    // Try install first. If already installed, skip param_config entirely —
    // calling i2c_param_config resets the I2C peripheral (i2c_hal_master_init)
    // and can corrupt in-progress bus state shared with other features.
    esp_err_t ret = i2c_driver_install(I2C_PORT, I2C_MODE_MASTER, 0, 0, 0);
    if (ret == ESP_FAIL || ret == ESP_ERR_INVALID_STATE) {
        return ESP_OK;  // Already installed by another feature
    }
    if (ret != ESP_OK) return ret;
    i2c_config_t cfg = {
        .mode             = I2C_MODE_MASTER,
        .sda_io_num       = I2C_PIN_SDA,
        .scl_io_num       = I2C_PIN_SCL,
        .sda_pullup_en    = GPIO_PULLUP_ENABLE,
        .scl_pullup_en    = GPIO_PULLUP_ENABLE,
        .master.clk_speed = 400000,
    };
    return i2c_param_config(I2C_PORT, &cfg);
}

esp_err_t imu_init(void)
{
    ESP_ERROR_CHECK(init_i2c_bus());

    uint8_t who_am_i = 0;
    esp_err_t ret = i2c_read_regs(REG_WHO_AM_I, &who_am_i, 1);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Failed to read WHO_AM_I: %s", esp_err_to_name(ret));
        return ret;
    }
    if (who_am_i != QMI8658_WHO_AM_I) {
        ESP_LOGW(TAG, "Unexpected WHO_AM_I: 0x%02X (expected 0x%02X)", who_am_i, QMI8658_WHO_AM_I);
    }

    // Enable accel (4g, 125Hz ODR) and gyro (512dps, 125Hz ODR)
    ESP_ERROR_CHECK(i2c_write_reg(REG_CTRL2, 0x23));  // accel 4g, 125Hz
    ESP_ERROR_CHECK(i2c_write_reg(REG_CTRL3, 0x53));  // gyro 512dps, 125Hz
    ESP_ERROR_CHECK(i2c_write_reg(REG_CTRL7, 0x03));  // enable accel + gyro

    ESP_LOGI(TAG, "QMI8658 IMU ready (WHO_AM_I=0x%02X)", who_am_i);
    return ESP_OK;
}

esp_err_t imu_read(imu_data_t *out)
{
    uint8_t raw[12];
    esp_err_t ret = i2c_read_regs(REG_ACCEL_X_L, raw, sizeof(raw));
    if (ret != ESP_OK) return ret;

    int16_t ax = (int16_t)((raw[1]  << 8) | raw[0]);
    int16_t ay = (int16_t)((raw[3]  << 8) | raw[2]);
    int16_t az = (int16_t)((raw[5]  << 8) | raw[4]);
    int16_t gx = (int16_t)((raw[7]  << 8) | raw[6]);
    int16_t gy = (int16_t)((raw[9]  << 8) | raw[8]);
    int16_t gz = (int16_t)((raw[11] << 8) | raw[10]);

    // 4g range: 1 LSB = 4/32768 g = 0.000122 g = 0.001197 m/s²
    const float accel_scale = 4.0f * 9.81f / 32768.0f;
    // 512dps range: 1 LSB = 512/32768 deg/s = 0.015625 deg/s
    const float gyro_scale = 512.0f / 32768.0f;

    out->accel_x = ax * accel_scale;
    out->accel_y = ay * accel_scale;
    out->accel_z = az * accel_scale;
    out->gyro_x  = gx * gyro_scale;
    out->gyro_y  = gy * gyro_scale;
    out->gyro_z  = gz * gyro_scale;
    return ESP_OK;
}
