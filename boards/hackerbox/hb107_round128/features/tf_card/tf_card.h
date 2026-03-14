// Copyright 2025 David M. King
// SPDX-License-Identifier: Apache-2.0

#pragma once
#include "esp_err.h"

// Mount the SD card over SPI. Call after board_init() — shares SPI2_HOST
// with the GC9A01 display. Mount point: CONFIG_TF_CARD_MOUNT_POINT (/sdcard).
esp_err_t tf_card_init(void);
