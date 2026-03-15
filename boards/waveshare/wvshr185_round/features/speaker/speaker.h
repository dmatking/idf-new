// Copyright 2025-2026 David M. King
// SPDX-License-Identifier: Apache-2.0

#pragma once
#include "esp_err.h"
#include <stdint.h>
#include <stddef.h>

// I2S speaker output (LRCK=IO38, DIN=IO47, BCK=IO48).
// Sample rate and bits configurable via menuconfig.

esp_err_t speaker_init(void);

// Write PCM samples. Blocks until written.
esp_err_t speaker_write(const int16_t *samples, size_t num_samples, size_t *written);
