// Minimal CST226 touch bring-up (no gesture handling)
#include "touch_min.h"
#include "product_pins.h"
#include "i2c_driver.h"
#include "esp_log.h"
#include "driver/gpio.h"
#include "driver/i2c_master.h"
#include <string.h>
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#define CST226_ADDR 0x5A

static const char *TAG = "TOUCH_MIN";
static i2c_master_dev_handle_t s_touch_dev = NULL;

static esp_err_t cst226_write(uint8_t reg, const uint8_t *data, size_t len)
{
    uint8_t buf[1 + 8];
    if (len > sizeof(buf) - 1) return ESP_ERR_INVALID_ARG;
    buf[0] = reg;
    if (len) memcpy(&buf[1], data, len);
    return i2c_master_transmit(s_touch_dev, buf, len + 1, 1000);
}

bool touch_min_init(void)
{
#ifdef BOARD_TOUCH_RST
    gpio_config_t rst_cfg = {
        .pin_bit_mask = 1ULL << BOARD_TOUCH_RST,
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    ESP_ERROR_CHECK(gpio_config(&rst_cfg));
    gpio_set_level(BOARD_TOUCH_RST, 0);
    vTaskDelay(pdMS_TO_TICKS(10));
    gpio_set_level(BOARD_TOUCH_RST, 1);
    vTaskDelay(pdMS_TO_TICKS(50));
#endif

#ifdef BOARD_TOUCH_IRQ
    if (BOARD_TOUCH_IRQ != -1) {
        gpio_config_t irq_cfg = {
            .pin_bit_mask = 1ULL << BOARD_TOUCH_IRQ,
            .mode = GPIO_MODE_INPUT,
            .pull_up_en = GPIO_PULLUP_ENABLE,
            .pull_down_en = GPIO_PULLDOWN_DISABLE,
            .intr_type = GPIO_INTR_DISABLE,
        };
        ESP_ERROR_CHECK(gpio_config(&irq_cfg));
    }
#endif

    esp_err_t ok = i2c_master_probe(bus_handle, CST226_ADDR, 1000);
    if (ok != ESP_OK) {
        ESP_LOGW(TAG, "probe 0x%02X failed: 0x%x", CST226_ADDR, ok);
        return false;
    }

    if (!s_touch_dev) {
        i2c_device_config_t dev_cfg = {
            .dev_addr_length = I2C_ADDR_BIT_LEN_7,
            .device_address = CST226_ADDR,
            .scl_speed_hz = 400000,
        };
        ESP_ERROR_CHECK(i2c_master_bus_add_device(bus_handle, &dev_cfg, &s_touch_dev));
    }

    // Enter command mode and read checkcode (matches vendor init)
    uint8_t val = 0x01;
    cst226_write(0xD1, &val, 1);
    vTaskDelay(pdMS_TO_TICKS(10));

    uint8_t check[4] = {0};
    uint8_t cmd_fc[2] = {0xD1, 0xFC};
    if (i2c_master_transmit_receive(s_touch_dev, cmd_fc, sizeof(cmd_fc), check, sizeof(check), 1000) == ESP_OK) {
        uint32_t code = ((uint32_t)check[3] << 24) | ((uint32_t)check[2] << 16) | ((uint32_t)check[1] << 8) | check[0];
        ESP_LOGI(TAG, "CST226 checkcode 0x%08lx", (unsigned long)code);
    } else {
        ESP_LOGW(TAG, "CST226 checkcode read failed");
    }

    // Exit command mode
    val = 0x09;
    cst226_write(0xD1, &val, 1);

    return true;
}
