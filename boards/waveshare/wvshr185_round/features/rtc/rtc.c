// Copyright 2025-2026 David M. King
// SPDX-License-Identifier: Apache-2.0

// PCF85063 RTC over I2C
// I2C bus: SCL=IO10, SDA=IO11 (shared with IMU and IO expander)
// I2C address: 0x51
// Note: this board uses a PCF85063 (NOT PCF8563) — time registers start at 0x04.

#include "rtc.h"
#include "driver/i2c.h"
#include "esp_log.h"

static const char *TAG = "RTC";

#define I2C_PORT        CONFIG_RTC_I2C_PORT
#define I2C_PIN_SCL     10
#define I2C_PIN_SDA     11
#define PCF85063_ADDR   0x51

// PCF85063 register map
#define REG_CTRL1       0x00
#define REG_CTRL2       0x01
#define REG_SECONDS     0x04    // BCD, bit7 = OS (oscillator stop)
#define REG_MINUTES     0x05    // BCD, mask 0x7F
#define REG_HOURS       0x06    // BCD, mask 0x3F
#define REG_DAY         0x07    // BCD, mask 0x3F
#define REG_WEEKDAY     0x08    // 0–6
#define REG_MONTH       0x09    // BCD, mask 0x1F
#define REG_YEAR        0x0A    // BCD 0–99

// CTRL1 bits
#define CTRL1_CAP_SEL   0x01    // 12.5pF load capacitance

static uint8_t bcd2dec(uint8_t bcd) { return (bcd >> 4) * 10 + (bcd & 0x0F); }
static uint8_t dec2bcd(uint8_t dec) { return ((dec / 10) << 4) | (dec % 10); }

static esp_err_t i2c_read_regs(uint8_t reg, uint8_t *data, size_t len)
{
    return i2c_master_write_read_device(I2C_PORT, PCF85063_ADDR, &reg, 1, data, len, pdMS_TO_TICKS(50));
}

static esp_err_t i2c_write_reg(uint8_t reg, uint8_t val)
{
    uint8_t buf[2] = {reg, val};
    return i2c_master_write_to_device(I2C_PORT, PCF85063_ADDR, buf, sizeof(buf), pdMS_TO_TICKS(50));
}

static esp_err_t init_i2c_bus(void)
{
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

esp_err_t rtc_clock_init(void)
{
    ESP_ERROR_CHECK(init_i2c_bus());
    // Normal mode, RTC run, 12.5pF cap (matches vendor demo)
    esp_err_t ret = i2c_write_reg(REG_CTRL1, CTRL1_CAP_SEL);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "PCF85063 init failed: %s", esp_err_to_name(ret));
        return ret;
    }
    ESP_LOGI(TAG, "PCF85063 RTC ready");
    return ESP_OK;
}

esp_err_t rtc_get_time(rtc_time_t *out)
{
    uint8_t raw[7];
    esp_err_t ret = i2c_read_regs(REG_SECONDS, raw, sizeof(raw));
    if (ret != ESP_OK) return ret;

    out->seconds = bcd2dec(raw[0] & 0x7F);
    out->minutes = bcd2dec(raw[1] & 0x7F);
    out->hours   = bcd2dec(raw[2] & 0x3F);
    out->day     = bcd2dec(raw[3] & 0x3F);
    out->month   = bcd2dec(raw[5] & 0x1F);
    out->year    = 2000 + bcd2dec(raw[6]);
    return ESP_OK;
}

esp_err_t rtc_set_time(const rtc_time_t *t)
{
    uint8_t buf[8];
    buf[0] = REG_SECONDS;
    buf[1] = dec2bcd(t->seconds);
    buf[2] = dec2bcd(t->minutes);
    buf[3] = dec2bcd(t->hours);
    buf[4] = dec2bcd(t->day);
    buf[5] = 0x00;                          // weekday (not tracked)
    buf[6] = dec2bcd(t->month);
    buf[7] = dec2bcd((uint8_t)(t->year - 2000));
    return i2c_master_write_to_device(I2C_PORT, PCF85063_ADDR, buf, sizeof(buf), pdMS_TO_TICKS(50));
}
