// Copyright 2025 David M. King
// SPDX-License-Identifier: Apache-2.0

#pragma once
#include "esp_err.h"
#include <stdint.h>
#include <stddef.h>

// PDM microphone input (SCK=IO15, WS=IO2, SD=IO39).
// Sample rate and bits configurable via menuconfig.

esp_err_t mic_init(void);

// Read PCM samples. Blocks until num_samples are available.
esp_err_t mic_read(int16_t *samples, size_t num_samples, size_t *read_count);
