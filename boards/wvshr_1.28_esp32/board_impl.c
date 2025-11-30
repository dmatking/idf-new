// Copyright 2025 David M. King
// SPDX-License-Identifier: Apache-2.0

#include "board_if.h"
#include "esp_log.h"

#include "driver/spi_master.h"
#include "esp_lcd_panel_ops.h"
#include "esp_lcd_panel_io.h"
#include "esp_lcd_gc9a01.h"

#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

// --- HARDWARE CONFIGURATION (Plain ESP32) ---
#define LCD_HOST        SPI2_HOST

#define PIN_NUM_MISO    -1         // Not used for LCD
#define PIN_NUM_CLK     14         // SCK
#define PIN_NUM_MOSI    15         // MOSI
#define PIN_NUM_CS      5          // CS
#define PIN_NUM_DC      27         // DC
#define PIN_NUM_RST     33         // RST
#define PIN_NUM_BK_LIGHT 22        // Backlight (if you want to use it)

#define LCD_H_RES       240
#define LCD_V_RES       240

static const char *TAG = "WVSHR_128_ESP32";
static esp_lcd_panel_handle_t panel = NULL;

// Helper: fill entire screen with a solid color using draw_bitmap
static void fill_screen(uint16_t color)
{
    if (!panel) return;

    // 1 line of pixels (RGB565)
    static uint16_t line[LCD_H_RES];

    for (int x = 0; x < LCD_H_RES; x++) {
        line[x] = color;
    }

    // Draw one line at a time
    for (int y = 0; y < LCD_V_RES; y++) {
        esp_lcd_panel_draw_bitmap(
            panel,
            0, y,
            LCD_H_RES, y + 1,
            line
        );
    }
}

void board_init(void)
{
    ESP_LOGI(TAG, "Init Waveshare 1.28 Round esp32-d0 no touch board");

    spi_bus_config_t buscfg = {
        .sclk_io_num = PIN_NUM_CLK,
        .mosi_io_num = PIN_NUM_MOSI,
        .miso_io_num = PIN_NUM_MISO,
        .quadwp_io_num = -1,
        .quadhd_io_num = -1,
        .max_transfer_sz = LCD_H_RES * 240 * sizeof(uint16_t) + 100,
    };
    ESP_ERROR_CHECK(spi_bus_initialize(LCD_HOST, &buscfg, SPI_DMA_CH_AUTO));

    esp_lcd_panel_io_handle_t io = NULL;
    esp_lcd_panel_io_spi_config_t io_cfg = {
        .dc_gpio_num = PIN_NUM_DC,
        .cs_gpio_num = PIN_NUM_CS,
        .pclk_hz = 40 * 1000 * 1000, // 40MHz
        .lcd_cmd_bits = 8,
        .lcd_param_bits = 8,
        .spi_mode = 0,
        .trans_queue_depth = 10,
    };
    ESP_ERROR_CHECK(esp_lcd_new_panel_io_spi(
        (esp_lcd_spi_bus_handle_t)LCD_HOST,
        &io_cfg,
        &io
    ));

    esp_lcd_panel_dev_config_t panel_cfg = {
        .reset_gpio_num = PIN_NUM_RST,
        .rgb_endian = LCD_RGB_ENDIAN_BGR,
        .bits_per_pixel = 16,
    };
    ESP_ERROR_CHECK(esp_lcd_new_panel_gc9a01(io, &panel_cfg, &panel));
    ESP_ERROR_CHECK(esp_lcd_panel_reset(panel));
    ESP_ERROR_CHECK(esp_lcd_panel_init(panel));
    ESP_ERROR_CHECK(esp_lcd_panel_mirror(panel, true, false));

    ESP_LOGI(TAG, "Waveshare 1.28 Round esp32-d0 init done.");
}

const char *board_get_name(void)
{
    return "Waveshare 1.28 Round esp32-d0";
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
    uint16_t black = 0x0000;

    esp_lcd_panel_disp_on_off(panel, true);

    fill_screen(red);
    vTaskDelay(pdMS_TO_TICKS(250));

    fill_screen(green);
    vTaskDelay(pdMS_TO_TICKS(250));

    fill_screen(blue);
    vTaskDelay(pdMS_TO_TICKS(250));

    fill_screen(black);
    vTaskDelay(pdMS_TO_TICKS(250));
}
