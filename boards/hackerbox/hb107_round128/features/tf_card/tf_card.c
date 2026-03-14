// Copyright 2025 David M. King
// SPDX-License-Identifier: Apache-2.0

#include "tf_card.h"
#include "esp_log.h"
#include "esp_vfs_fat.h"
#include "driver/sdspi_host.h"
#include "sdmmc_cmd.h"

static const char *TAG = "TF_CARD";

// Shares SPI2_HOST (CLK=IO14, MOSI=IO15) with the GC9A01 display.
// board_init() must be called first so the SPI bus is already initialized.
#define SD_SPI_HOST     SPI2_HOST
#define SD_PIN_CS       13      // DATA3
#define SD_PIN_MISO     2       // DATA0 — added to bus in board_impl.c

static sdmmc_card_t *s_card = NULL;

esp_err_t tf_card_init(void)
{
    esp_vfs_fat_sdmmc_mount_config_t mount_cfg = {
        .format_if_mount_failed = false,
        .max_files = CONFIG_TF_CARD_MAX_FILES,
        .allocation_unit_size = 16 * 1024,
    };

    sdmmc_host_t host = SDSPI_HOST_DEFAULT();
    host.slot = SD_SPI_HOST;

    sdspi_device_config_t slot_cfg = SDSPI_DEVICE_CONFIG_DEFAULT();
    slot_cfg.gpio_cs   = SD_PIN_CS;
    slot_cfg.gpio_cd   = SDSPI_SLOT_NO_CD;
    slot_cfg.gpio_wp   = SDSPI_SLOT_NO_WP;

    esp_err_t ret = esp_vfs_fat_sdspi_mount(
        CONFIG_TF_CARD_MOUNT_POINT, &host, &slot_cfg, &mount_cfg, &s_card);

    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "Mount failed: %s", esp_err_to_name(ret));
        return ret;
    }

    sdmmc_card_print_info(stdout, s_card);
    ESP_LOGI(TAG, "SD card mounted at %s", CONFIG_TF_CARD_MOUNT_POINT);
    return ESP_OK;
}
