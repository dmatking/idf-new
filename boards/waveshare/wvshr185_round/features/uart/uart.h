// Copyright 2025 David M. King
// SPDX-License-Identifier: Apache-2.0

#pragma once
#include "esp_err.h"
#include <stdint.h>
#include <stddef.h>

// UART header (TX=IO43, RX=IO44).
// Port and baud rate configurable via menuconfig.

esp_err_t uart_header_init(void);

// Write bytes. Returns ESP_OK on success.
esp_err_t uart_header_write(const uint8_t *data, size_t len);

// Read up to max_len bytes. Returns number of bytes read (>=0) or <0 on error.
int uart_header_read(uint8_t *buf, size_t max_len, uint32_t timeout_ms);
