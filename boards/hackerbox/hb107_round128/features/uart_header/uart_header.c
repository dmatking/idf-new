// Copyright 2025-2026 David M. King
// SPDX-License-Identifier: Apache-2.0

#include "uart_header.h"
#include "driver/uart.h"
#include "driver/gpio.h"
#include "esp_log.h"

static const char *TAG = "UART_HEADER";

#define UART_PIN_TX     26
#define UART_PIN_RX     25
#define UART_BUF_SIZE   1024

esp_err_t uart_header_init(void)
{
    uart_config_t cfg = {
        .baud_rate  = CONFIG_UART_HEADER_BAUD,
        .data_bits  = UART_DATA_8_BITS,
        .parity     = UART_PARITY_DISABLE,
        .stop_bits  = UART_STOP_BITS_1,
        .flow_ctrl  = UART_HW_FLOWCTRL_DISABLE,
    };

    esp_err_t ret = uart_param_config(CONFIG_UART_HEADER_PORT, &cfg);
    if (ret != ESP_OK) return ret;

    ret = uart_set_pin(CONFIG_UART_HEADER_PORT,
                       UART_PIN_TX, UART_PIN_RX,
                       UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);
    if (ret != ESP_OK) return ret;

    ret = uart_driver_install(CONFIG_UART_HEADER_PORT, UART_BUF_SIZE, 0, 0, NULL, 0);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "uart_driver_install failed: %s", esp_err_to_name(ret));
        return ret;
    }

    ESP_LOGI(TAG, "UART%d ready (TX=%d RX=%d @ %d baud)",
             CONFIG_UART_HEADER_PORT, UART_PIN_TX, UART_PIN_RX, CONFIG_UART_HEADER_BAUD);
    return ESP_OK;
}
