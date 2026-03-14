// Copyright 2025 David M. King
// SPDX-License-Identifier: Apache-2.0

#pragma once

#include <stdbool.h>
#include <stdint.h>
#include <time.h>

#ifdef __cplusplus
extern "C" {
#endif

// Parsed GPS state. Updated by the background reader task; read via gps_get_state().
typedef struct {
    bool gga_fix;           // GGA sentence reports a fix
    bool rmc_fix;           // RMC sentence reports active status (A or D)
    bool latlon_valid;      // latitude_deg / longitude_deg are valid
    bool time_valid;        // utc_tm time fields are valid
    bool date_valid;        // utc_tm date fields are valid
    bool speed_valid;       // speed_knots is valid
    double latitude_deg;    // decimal degrees, negative = south
    double longitude_deg;   // decimal degrees, negative = west
    float speed_knots;
    float heading_deg;      // true track from RMC
    int sats_in_use;
    struct tm utc_tm;       // UTC time/date (populated incrementally from GGA + RMC)
} gps_state_t;

// Initialize UART and start the background reader task.
// Pins and baud rate are taken from Kconfig (CONFIG_GPS_UART_PORT, CONFIG_GPS_RX_PIN, etc.)
void gps_init(void);

// Thread-safe snapshot of the current GPS state.
gps_state_t gps_get_state(void);

// True if either GGA or RMC reports a fix.
bool gps_has_fix(void);

#ifdef __cplusplus
}
#endif
