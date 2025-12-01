// Copyright 2025 David M. King
// SPDX-License-Identifier: Apache-2.0


//Coming soon

#include "board_interface.h"
#include "esp_log.h"

static const char *TAG = "BOARD_GENERIC";

void board_init(void)
{
    ESP_LOGI(TAG, "Generic ESP32 board init (no LCD).");
}

const char *board_get_name(void)
{
    return "Generic ESP32";
}

bool board_has_lcd(void)
{
    return false;
}

void board_lcd_sanity_test(void)
{
    ESP_LOGI(TAG, "No LCD; skipping sanity test.");
}
