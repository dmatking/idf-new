// Copyright 2025-2026 David M. King
// SPDX-License-Identifier: Apache-2.0
//
// Board implementation for Espressif ESP32-S31-Korvo
// 800x480 16-bit RGB parallel LCD, GT1151 capacitive touch
//
// Pin definitions match the vendor BSP (esp-dev-kits/examples/esp32-s31-korvo).
// Requires IDF >= 6.1.0 (esp32s31 target).

#include "board_interface.h"

#include <string.h>
#include "driver/gpio.h"
#include "driver/i2c_master.h"
#include "esp_cache.h"
#include "esp_heap_caps.h"
#include "esp_lcd_panel_io.h"
#include "esp_lcd_panel_ops.h"
#include "esp_lcd_panel_rgb.h"
#include "esp_lcd_touch_gt1151.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

static const char *TAG = "BOARD_S31_KORVO";

#define BOARD_NAME "Espressif ESP32-S31-Korvo"

#define LCD_W  800
#define LCD_H  480
#define BPP    2    // RGB565: 2 bytes per pixel

#define LCD_PCLK_HZ  (26 * 1000 * 1000)

// 16-bit RGB data bus GPIOs (matches vendor BSP pin order: B[3:7], G[2:7], R[3:7])
#define LCD_D0  8   // B3
#define LCD_D1  9   // B4
#define LCD_D2  10  // B5
#define LCD_D3  11  // B6
#define LCD_D4  12  // B7
#define LCD_D5  13  // G2
#define LCD_D6  14  // G3
#define LCD_D7  15  // G4
#define LCD_D8  16  // G5
#define LCD_D9  17  // G6
#define LCD_D10 18  // G7
#define LCD_D11 19  // R3
#define LCD_D12 33  // R4
#define LCD_D13 34  // R5
#define LCD_D14 35  // R6
#define LCD_D15 36  // R7

#define LCD_PCLK   40
#define LCD_DE     43
#define LCD_HSYNC  44
#define LCD_VSYNC  45
// Backlight and DISP_EN are NC on this board.

// Shared I2C bus (touch uses this)
#define I2C_SDA  0
#define I2C_SCL  1

#define FB_SIZE_BYTES ((size_t)(LCD_W) * (LCD_H) * (BPP))

static esp_lcd_panel_handle_t  s_panel = NULL;
static esp_lcd_touch_handle_t  s_touch = NULL;
static uint16_t               *s_fb    = NULL;  // panel's internal PSRAM framebuffer
static bool                    s_touch_task_started = false;

// --- Touch logger (background task, not part of board_interface.h) ---

static void touch_logger_task(void *arg)
{
    bool touching = false;
    for (;;) {
        if (s_touch) {
            esp_lcd_touch_point_data_t pts[1] = {0};
            uint8_t cnt = 0;
            esp_lcd_touch_read_data(s_touch);
            bool pressed = (esp_lcd_touch_get_data(s_touch, pts, &cnt, 1) == ESP_OK) && (cnt > 0);
            if (pressed) {
                touching = true;
                ESP_LOGI(TAG, "Touch (%u,%u)", (unsigned)pts[0].x, (unsigned)pts[0].y);
            } else if (touching) {
                touching = false;
                ESP_LOGI(TAG, "Touch released");
            }
        }
        vTaskDelay(pdMS_TO_TICKS(50));
    }
}

static void start_touch_logger(void)
{
    if (s_touch_task_started) {
        return;
    }
    BaseType_t ok = xTaskCreate(touch_logger_task, "TouchLog", 2048, NULL, 5, NULL);
    if (ok == pdPASS) {
        s_touch_task_started = true;
    } else {
        ESP_LOGW(TAG, "touch logger task create failed");
    }
}

// --- Touch init (optional, does not abort board_init on failure) ---

static void init_touch(void)
{
    i2c_master_bus_handle_t i2c_bus = NULL;
    const i2c_master_bus_config_t i2c_cfg = {
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .sda_io_num = I2C_SDA,
        .scl_io_num = I2C_SCL,
        .i2c_port   = I2C_NUM_0,
        .flags.enable_internal_pullup = true,
    };
    esp_err_t ret = i2c_new_master_bus(&i2c_cfg, &i2c_bus);
    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "I2C bus init failed (%s), no touch", esp_err_to_name(ret));
        return;
    }

    esp_lcd_panel_io_i2c_config_t tp_io_cfg = ESP_LCD_TOUCH_IO_I2C_GT1151_CONFIG();
    tp_io_cfg.scl_speed_hz = 400000;
    esp_lcd_panel_io_handle_t tp_io = NULL;
    ret = esp_lcd_new_panel_io_i2c(i2c_bus, &tp_io_cfg, &tp_io);
    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "touch panel IO init failed (%s)", esp_err_to_name(ret));
        return;
    }

    const esp_lcd_touch_config_t touch_cfg = {
        .x_max        = LCD_W,
        .y_max        = LCD_H,
        .rst_gpio_num = GPIO_NUM_NC,
        .int_gpio_num = GPIO_NUM_NC,
        .levels = { .reset = 0, .interrupt = 0 },
        .flags  = { .swap_xy = 0, .mirror_x = 0, .mirror_y = 0 },
    };
    ret = esp_lcd_touch_new_i2c_gt1151(tp_io, &touch_cfg, &s_touch);
    if (ret != ESP_OK) {
        ESP_LOGW(TAG, "GT1151 init failed (%s), continuing without touch", esp_err_to_name(ret));
        return;
    }
    start_touch_logger();
}

// --- board_interface.h implementation ---

void board_init(void)
{
    ESP_LOGI(TAG, "%s init", BOARD_NAME);

    // RGB panel — single PSRAM framebuffer, 16-bit RGB565, 800x480
    esp_lcd_rgb_panel_config_t panel_cfg = {
        .clk_src = LCD_CLK_SRC_DEFAULT,
        .timings = {
            .pclk_hz           = LCD_PCLK_HZ,
            .h_res             = LCD_W,
            .v_res             = LCD_H,
            .hsync_pulse_width = 1,
            .hsync_back_porch  = 40,
            .hsync_front_porch = 20,
            .vsync_pulse_width = 1,
            .vsync_back_porch  = 10,
            .vsync_front_porch = 5,
            .flags = {
                .pclk_active_neg = true,
            },
        },
        .data_width      = 16,
        .in_color_format = LCD_COLOR_FMT_RGB565,
        .num_fbs         = 1,
        .dma_burst_size  = 64,
        .hsync_gpio_num  = LCD_HSYNC,
        .vsync_gpio_num  = LCD_VSYNC,
        .de_gpio_num     = LCD_DE,
        .pclk_gpio_num   = LCD_PCLK,
        .disp_gpio_num   = GPIO_NUM_NC,
        .data_gpio_nums = {
            LCD_D0,  LCD_D1,  LCD_D2,  LCD_D3,
            LCD_D4,  LCD_D5,  LCD_D6,  LCD_D7,
            LCD_D8,  LCD_D9,  LCD_D10, LCD_D11,
            LCD_D12, LCD_D13, LCD_D14, LCD_D15,
            GPIO_NUM_NC, GPIO_NUM_NC, GPIO_NUM_NC, GPIO_NUM_NC,
            GPIO_NUM_NC, GPIO_NUM_NC, GPIO_NUM_NC, GPIO_NUM_NC,
        },
        .flags = {
            .fb_in_psram = true,
        },
    };
    ESP_ERROR_CHECK(esp_lcd_new_rgb_panel(&panel_cfg, &s_panel));
    ESP_ERROR_CHECK(esp_lcd_panel_reset(s_panel));
    ESP_ERROR_CHECK(esp_lcd_panel_init(s_panel));

    // Get direct pointer to the panel's internal PSRAM framebuffer.
    // CPU writes go here; esp_cache_msync flushes them to PSRAM for the DMA scanner.
    void *fb_ptr = NULL;
    ESP_ERROR_CHECK(esp_lcd_rgb_panel_get_frame_buffer(s_panel, 1, &fb_ptr));
    s_fb = (uint16_t *)fb_ptr;
    memset(s_fb, 0, FB_SIZE_BYTES);
    board_lcd_flush();

    init_touch();

    ESP_LOGI(TAG, "%s init done", BOARD_NAME);
}

const char *board_get_name(void) { return BOARD_NAME; }
bool        board_has_lcd(void)  { return s_fb != NULL; }

int board_lcd_width(void)  { return LCD_W; }
int board_lcd_height(void) { return LCD_H; }

// Flush: push CPU cache lines to PSRAM so the RGB DMA scanner picks up the changes.
void board_lcd_flush(void)
{
    if (!s_fb) {
        return;
    }
    esp_cache_msync(s_fb, FB_SIZE_BYTES, ESP_CACHE_MSYNC_FLAG_DIR_C2M);
}

// Region flush: sync only the affected rows (full row width; partial rows expand to full).
// 800 px * 2 B = 1600 B per row, which is a multiple of 64 B (cache line), so always aligned.
void board_lcd_flush_region(int x1, int y1, int x2, int y2)
{
    if (!s_fb) {
        return;
    }
    (void)x1;
    (void)x2;
    const size_t row_bytes = (size_t)LCD_W * BPP;
    void  *start = (uint8_t *)s_fb + (size_t)y1 * row_bytes;
    size_t len   = (size_t)(y2 - y1) * row_bytes;
    esp_cache_msync(start, len, ESP_CACHE_MSYNC_FLAG_DIR_C2M);
}

void board_lcd_clear(void)
{
    if (s_fb) {
        memset(s_fb, 0, FB_SIZE_BYTES);
    }
}

void board_lcd_fill(uint16_t color)
{
    if (!s_fb) {
        return;
    }
    // RGB panel reads pixels without byte-swapping; store RGB565 as-is.
    uint16_t *p = s_fb;
    for (int i = 0; i < LCD_W * LCD_H; i++) {
        *p++ = color;
    }
    board_lcd_flush();
}

void board_lcd_set_pixel_raw(int x, int y, uint16_t color)
{
    if (s_fb && x >= 0 && x < LCD_W && y >= 0 && y < LCD_H) {
        s_fb[y * LCD_W + x] = color;
    }
}

void board_lcd_set_pixel_rgb(int x, int y, uint8_t r, uint8_t g, uint8_t b)
{
    if (s_fb && x >= 0 && x < LCD_W && y >= 0 && y < LCD_H) {
        s_fb[y * LCD_W + x] = board_lcd_pack_rgb(r, g, b);
    }
}

uint16_t board_lcd_pack_rgb(uint8_t r, uint8_t g, uint8_t b)
{
    // Standard RGB565, no byte-swap (RGB parallel panel reads the 16-bit word directly).
    return ((uint16_t)(r >> 3) << 11) | ((uint16_t)(g >> 2) << 5) | (b >> 3);
}

uint16_t board_lcd_get_pixel_raw(int x, int y)
{
    if (!s_fb || x < 0 || x >= LCD_W || y < 0 || y >= LCD_H) {
        return 0;
    }
    return s_fb[y * LCD_W + x];
}

void board_lcd_unpack_rgb(uint16_t color, uint8_t *r, uint8_t *g, uint8_t *b)
{
    *r = ((color >> 11) & 0x1F) << 3;
    *g = ((color >>  5) & 0x3F) << 2;
    *b = ((color >>  0) & 0x1F) << 3;
}

void board_lcd_sanity_test(void)
{
    if (!s_fb) {
        return;
    }
    ESP_LOGI(TAG, "Sanity test: cycling colors");
    static const struct { uint8_t r, g, b; } colors[] = {
        {255,   0,   0},
        {  0, 255,   0},
        {  0,   0, 255},
        {255, 255, 255},
        {  0,   0,   0},
    };
    for (int i = 0; i < 5; i++) {
        board_lcd_fill(board_lcd_pack_rgb(colors[i].r, colors[i].g, colors[i].b));
        vTaskDelay(pdMS_TO_TICKS(400));
    }
}
