// Copyright 2025 David M. King
// SPDX-License-Identifier: Apache-2.0

#include "board_if.h"
#include "esp_log.h"

#include "driver/spi_master.h"
#include "esp_lcd_panel_ops.h"
#include "esp_lcd_panel_io.h"
#include "esp_lcd_st7789.h" // or whatever this one uses

static const char *TAG = "BOARD_TDISPLAY_S3";
static esp_lcd_panel_handle_t panel = NULL;

void board_init(void)
{
    ESP_LOGI(TAG, "Init T-Display S3 board");

    // TODO: real pins for your specific module
    spi_bus_config_t buscfg = {
        .sclk_io_num = 36,
        .mosi_io_num = 35,
        .miso_io_num = -1,
        .quadwp_io_num = -1,
        .quadhd_io_num = -1,
        .max_transfer_sz = 4096,
    };
    ESP_ERROR_CHECK(spi_bus_initialize(SPI2_HOST, &buscfg, SPI_DMA_CH_AUTO));

    esp_lcd_panel_io_handle_t io = NULL;
    esp_lcd_panel_io_spi_config_t io_cfg = {
        .cs_gpio_num = 34,
        .dc_gpio_num = 37,
        .spi_mode = 0,
        .pclk_hz = 40 * 1000 * 1000,
        .trans_queue_depth = 10,
    };
    ESP_ERROR_CHECK(esp_lcd_new_panel_io_spi((esp_lcd_spi_bus_handle_t)SPI2_HOST,
                                             &io_cfg, &io));

    esp_lcd_panel_dev_config_t panel_cfg = {
        .reset_gpio_num = 38,
        .rgb_endian = LCD_RGB_ENDIAN_RGB,
        .bits_per_pixel = 16,
    };
    ESP_ERROR_CHECK(esp_lcd_new_panel_st7789(io, &panel_cfg, &panel));
    ESP_ERROR_CHECK(esp_lcd_panel_reset(panel));
    ESP_ERROR_CHECK(esp_lcd_panel_init(panel));
    ESP_ERROR_CHECK(esp_lcd_panel_mirror(panel, false, false));

    ESP_LOGI(TAG, "T-Display S3 LCD init done.");
}

const char *board_get_name(void)
{
    return "LILYGO T-Display S3";
}

bool board_has_lcd(void)
{
    return panel != NULL;
}

void board_lcd_sanity_test(void)
{
    if (!panel) {
        ESP_LOGW(TAG, "Panel not initialized; skipping sanity test.");
        return;
    }

    ESP_LOGI(TAG, "Running LCD sanity test...");
    uint16_t red   = 0xF800;
    uint16_t green = 0x07E0;
    uint16_t blue  = 0x001F;

    esp_lcd_panel_disp_on_off(panel, true);
    esp_lcd_panel_fill(panel, 0, 0, 240, 135, red);
    vTaskDelay(pdMS_TO_TICKS(250));
    esp_lcd_panel_fill(panel, 0, 0, 240, 135, green);
    vTaskDelay(pdMS_TO_TICKS(250));
    esp_lcd_panel_fill(panel, 0, 0, 240, 135, blue);
    vTaskDelay(pdMS_TO_TICKS(250));
}
