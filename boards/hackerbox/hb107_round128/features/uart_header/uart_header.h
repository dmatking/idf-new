// Copyright 2025-2026 David M. King
// SPDX-License-Identifier: Apache-2.0

#pragma once
#include "esp_err.h"

// Initialize UART1 on the board's header pins (TX=IO26, RX=IO25).
// Port and baud rate are configured via menuconfig (CONFIG_UART_HEADER_*).
esp_err_t uart_header_init(void);
