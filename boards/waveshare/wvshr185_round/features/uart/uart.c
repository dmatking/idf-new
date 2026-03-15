// Copyright 2025 David M. King
// SPDX-License-Identifier: Apache-2.0

// UART header connector
// TX=IO43, RX=IO44

#include "uart.h"
#include "driver/uart.h"
#include "esp_log.h"

static const char *TAG = "UART_HDR";

#define UART_PORT       CONFIG_UART_HEADER_PORT
#define UART_PIN_TX     43
#define UART_PIN_RX     44
#define UART_BAUD       CONFIG_UART_HEADER_BAUD
#define UART_BUF_SIZE   256

esp_err_t uart_header_init(void)
{
    uart_config_t cfg = {
        .baud_rate  = UART_BAUD,
        .data_bits  = UART_DATA_8_BITS,
        .parity     = UART_PARITY_DISABLE,
        .stop_bits  = UART_STOP_BITS_1,
        .flow_ctrl  = UART_HW_FLOWCTRL_DISABLE,
    };
    esp_err_t ret = uart_param_config(UART_PORT, &cfg);
    if (ret != ESP_OK) return ret;

    ret = uart_set_pin(UART_PORT, UART_PIN_TX, UART_PIN_RX, UART_PIN_NO_CHANGE, UART_PIN_NO_CHANGE);
    if (ret != ESP_OK) return ret;

    ret = uart_driver_install(UART_PORT, UART_BUF_SIZE, 0, 0, NULL, 0);
    if (ret == ESP_ERR_INVALID_STATE) ret = ESP_OK;  // already installed
    if (ret != ESP_OK) return ret;

    ESP_LOGI(TAG, "UART ready (%d baud, TX=IO43, RX=IO44)", UART_BAUD);
    return ESP_OK;
}

esp_err_t uart_header_write(const uint8_t *data, size_t len)
{
    int sent = uart_write_bytes(UART_PORT, data, len);
    return (sent < 0) ? ESP_FAIL : ESP_OK;
}

int uart_header_read(uint8_t *buf, size_t max_len, uint32_t timeout_ms)
{
    return uart_read_bytes(UART_PORT, buf, max_len, pdMS_TO_TICKS(timeout_ms));
}
