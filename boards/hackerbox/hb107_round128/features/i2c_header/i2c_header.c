// Copyright 2025-2026 David M. King
// SPDX-License-Identifier: Apache-2.0

#include "i2c_header.h"
#include "driver/i2c.h"
#include "esp_log.h"

static const char *TAG = "I2C_HEADER";

#define I2C_PIN_SDA     21
#define I2C_PIN_SCL     22

esp_err_t i2c_header_init(void)
{
    i2c_config_t cfg = {
        .mode             = I2C_MODE_MASTER,
        .sda_io_num       = I2C_PIN_SDA,
        .scl_io_num       = I2C_PIN_SCL,
        .sda_pullup_en    = GPIO_PULLUP_ENABLE,
        .scl_pullup_en    = GPIO_PULLUP_ENABLE,
        .master.clk_speed = CONFIG_I2C_HEADER_CLK_HZ,
    };

    esp_err_t ret = i2c_param_config(CONFIG_I2C_HEADER_PORT, &cfg);
    if (ret != ESP_OK) return ret;

    ret = i2c_driver_install(CONFIG_I2C_HEADER_PORT, I2C_MODE_MASTER, 0, 0, 0);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "i2c_driver_install failed: %s", esp_err_to_name(ret));
        return ret;
    }

    ESP_LOGI(TAG, "I2C port %d ready (SDA=%d SCL=%d @ %dHz)",
             CONFIG_I2C_HEADER_PORT, I2C_PIN_SDA, I2C_PIN_SCL, CONFIG_I2C_HEADER_CLK_HZ);
    return ESP_OK;
}
