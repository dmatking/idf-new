// Copyright 2025 David M. King
// SPDX-License-Identifier: Apache-2.0

#pragma once
#include <stdbool.h>

void board_init(void);
const char *board_get_name(void);
bool board_has_lcd(void);

// Optional: implement to visually verify the LCD on startup.
// A default no-op is provided by board_defaults.c for headless boards.
void board_lcd_sanity_test(void);
