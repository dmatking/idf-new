// Copyright 2025 David M. King
// SPDX-License-Identifier: Apache-2.0

#include "board_interface.h"

#include <string.h>

#include "driver/gpio.h"
#include "driver/spi_master.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/task.h"

#define BOARD_NAME "LilyGO T4 S3 AMOLED Touch 2.41\""

#define LCD_HOST SPI3_HOST
#define LCD_H_RES 600
#define LCD_V_RES 450

// QSPI pins from LilyGo product_pins.h (CONFIG_LILYGO_T4_S3_241)
#define PIN_LCD_CS    11
#define PIN_LCD_SCK   15
#define PIN_LCD_D0    14
#define PIN_LCD_D1    10
#define PIN_LCD_D2    16
#define PIN_LCD_D3    12
#define PIN_LCD_RST   13
#define PIN_LCD_TE    -1
#define PIN_LCD_EN    9

#define LCD_SPI_FREQ_HZ (24 * 1000 * 1000)
#define LCD_SEND_CHUNK_PIXELS 16384

typedef struct {
    uint32_t addr;
    uint8_t param[20];
    uint32_t len;
} lcd_cmd_t;

static const lcd_cmd_t s_rm690b0_init[] = {
    {0xFE00, {0x20}, 0x01},
    {0x2600, {0x0A}, 0x01},
    {0x2400, {0x80}, 0x01},
    {0x5A00, {0x51}, 0x01},
    {0x5B00, {0x2E}, 0x01},
    {0xFE00, {0x00}, 0x01},
    {0x3A00, {0x55}, 0x01},
    {0xC200, {0x00}, 0x21},
    {0x3500, {0x00}, 0x01},
    {0x5100, {0x00}, 0x01},
    {0x1100, {0x00}, 0x80},
    {0x2900, {0x00}, 0x20},
    {0x5100, {0xFF}, 0x01},
};

static spi_device_handle_t s_spi = NULL;
static bool s_lcd_ready = false;
static uint16_t s_tx_buf[LCD_SEND_CHUNK_PIXELS];
static const char *TAG = "BOARD_T4S3_AMOLED";

static inline void panel_select(void)
{
    gpio_set_level(PIN_LCD_CS, 0);
}

static inline void panel_deselect(void)
{
    gpio_set_level(PIN_LCD_CS, 1);
}

static void amoled_write_cmd(uint32_t cmd, const uint8_t *data, uint32_t length)
{
    spi_transaction_t t = {0};
    t.flags = SPI_TRANS_MULTILINE_CMD | SPI_TRANS_MULTILINE_ADDR;
    t.cmd = 0x02;
    t.addr = cmd;
    t.length = length * 8;
    t.tx_buffer = data;
    panel_select();
    ESP_ERROR_CHECK(spi_device_polling_transmit(s_spi, &t));
    panel_deselect();
}

static void amoled_set_window(uint16_t xs, uint16_t ys, uint16_t xe, uint16_t ye)
{
    // Raw panel addressing with +16 column offset (per T4-S3)
    uint16_t xs_o = xs + 16;
    uint16_t xe_o = xe + 16;

    const uint8_t caset[] = {
        (uint8_t)((xs_o >> 8) & 0xFF), (uint8_t)(xs_o & 0xFF),
        (uint8_t)((xe_o >> 8) & 0xFF), (uint8_t)(xe_o & 0xFF),
    };
    const uint8_t raset[] = {
        (uint8_t)((ys >> 8) & 0xFF), (uint8_t)(ys & 0xFF),
        (uint8_t)((ye >> 8) & 0xFF), (uint8_t)(ye & 0xFF),
    };

    amoled_write_cmd(0x2A00, caset, sizeof(caset));
    amoled_write_cmd(0x2B00, raset, sizeof(raset));
    amoled_write_cmd(0x2C00, NULL, 0);
}

// Forward declaration
static void amoled_push_buffer(const uint16_t *data, size_t pixel_count);

static void draw_block_rotated(uint16_t lx, uint16_t ly, uint16_t w, uint16_t h, uint16_t color)
{
    // Logical coords (lx,ly) use LVGL-like space: lx in [0..LCD_V_RES), ly in [0..LCD_H_RES)
    uint16_t px = (LCD_H_RES - (ly + h));
    uint16_t py = lx;
    if (px > LCD_H_RES - 1) return;
    if (py > LCD_V_RES - 1) return;
    uint16_t pxe = px + h - 1;
    uint16_t pye = py + w - 1;
    if (pxe > LCD_H_RES - 1) pxe = LCD_H_RES - 1;
    if (pye > LCD_V_RES - 1) pye = LCD_V_RES - 1;

    static uint16_t block[50*50];
    uint32_t area = (uint32_t)(pxe - px + 1) * (uint32_t)(pye - py + 1);
    uint32_t chunk = sizeof(block) / sizeof(block[0]);
    for (uint32_t i = 0; i < chunk; ++i) block[i] = color;

    amoled_set_window(px, py, pxe, pye);
    uint32_t remaining = area;
    while (remaining) {
        uint32_t send = remaining > chunk ? chunk : remaining;
        amoled_push_buffer(block, send);
        remaining -= send;
    }
}

static void amoled_push_buffer(const uint16_t *data, size_t pixel_count)
{
    if (!s_spi || !pixel_count) {
        return;
    }
    bool first = true;
    size_t remaining = pixel_count;
    const uint16_t *p = data;

    panel_select();
    while (remaining) {
        size_t chunk = remaining;
        if (chunk > LCD_SEND_CHUNK_PIXELS) {
            chunk = LCD_SEND_CHUNK_PIXELS;
        }
        memcpy(s_tx_buf, p, chunk * sizeof(uint16_t));

        spi_transaction_ext_t t = {0};
        if (first) {
            t.base.flags = SPI_TRANS_MODE_QIO;
            t.base.cmd = 0x32;
            t.base.addr = 0x002C00;
            first = false;
        } else {
            t.base.flags = SPI_TRANS_MODE_QIO | SPI_TRANS_VARIABLE_CMD |
                       SPI_TRANS_VARIABLE_ADDR | SPI_TRANS_VARIABLE_DUMMY;
        }
        t.base.tx_buffer = s_tx_buf;
        t.base.length = chunk * 16;
        ESP_ERROR_CHECK(spi_device_polling_transmit(s_spi, (spi_transaction_t *)&t));
        p += chunk;
        remaining -= chunk;
    }
    panel_deselect();
}

static void panel_reset(void)
{
    vTaskDelay(pdMS_TO_TICKS(10));
    gpio_set_level(PIN_LCD_RST, 1);
    vTaskDelay(pdMS_TO_TICKS(20));
    gpio_set_level(PIN_LCD_RST, 0);
    vTaskDelay(pdMS_TO_TICKS(30));
    gpio_set_level(PIN_LCD_RST, 1);
    vTaskDelay(pdMS_TO_TICKS(20));
}

static esp_err_t init_display(void)
{
    gpio_config_t out_cfg = {
        .pin_bit_mask = (1ULL << PIN_LCD_CS) | (1ULL << PIN_LCD_RST),
        .mode = GPIO_MODE_OUTPUT,
        .pull_up_en = GPIO_PULLUP_DISABLE,
        .pull_down_en = GPIO_PULLDOWN_DISABLE,
        .intr_type = GPIO_INTR_DISABLE,
    };
    ESP_ERROR_CHECK(gpio_config(&out_cfg));
    gpio_set_level(PIN_LCD_CS, 1);

    if (PIN_LCD_EN >= 0) {
        gpio_config_t en_cfg = out_cfg;
        en_cfg.pin_bit_mask = 1ULL << PIN_LCD_EN;
        ESP_ERROR_CHECK(gpio_config(&en_cfg));
        gpio_set_level(PIN_LCD_EN, 1);
    }

    vTaskDelay(pdMS_TO_TICKS(120));
    panel_reset();

    spi_bus_config_t buscfg = {
        .data0_io_num = PIN_LCD_D0,
        .data1_io_num = PIN_LCD_D1,
        .sclk_io_num = PIN_LCD_SCK,
        .data2_io_num = PIN_LCD_D2,
        .data3_io_num = PIN_LCD_D3,
        .data4_io_num = -1,
        .data5_io_num = -1,
        .data6_io_num = -1,
        .data7_io_num = -1,
        .max_transfer_sz = (LCD_SEND_CHUNK_PIXELS * 16) + 8,
        .flags = SPICOMMON_BUSFLAG_MASTER | SPICOMMON_BUSFLAG_GPIO_PINS,
    };

    spi_device_interface_config_t devcfg = {
        .command_bits = 8,
        .address_bits = 24,
        .mode = 0,
        .clock_speed_hz = LCD_SPI_FREQ_HZ,
        .spics_io_num = -1,
        .flags = SPI_DEVICE_HALFDUPLEX,
        .queue_size = 10,
    };

    ESP_ERROR_CHECK(spi_bus_initialize(LCD_HOST, &buscfg, SPI_DMA_CH_AUTO));
    ESP_ERROR_CHECK(spi_bus_add_device(LCD_HOST, &devcfg, &s_spi));

    for (int retry = 0; retry < 2; ++retry) {
        for (size_t i = 0; i < (sizeof(s_rm690b0_init) / sizeof(s_rm690b0_init[0])); ++i) {
            const lcd_cmd_t *cmd = &s_rm690b0_init[i];
            uint32_t payload = cmd->len & 0x1F;
            if (payload > 0) {
                amoled_write_cmd(cmd->addr, cmd->param, payload);
            } else {
                amoled_write_cmd(cmd->addr, NULL, 0);
            }
            if (cmd->len & 0x80) {
                vTaskDelay(pdMS_TO_TICKS(120));
            } else if (cmd->len & 0x20) {
                vTaskDelay(pdMS_TO_TICKS(10));
            }
        }
    }

    s_lcd_ready = true;
    ESP_LOGI(TAG, "AMOLED ready (%dx%d)", LCD_H_RES, LCD_V_RES);
    return ESP_OK;
}

static void fill_screen(uint16_t color)
{
    if (!s_lcd_ready) {
        return;
    }

    static uint16_t line[LCD_H_RES];
    for (int x = 0; x < LCD_H_RES; ++x) {
        line[x] = color;
    }

    for (int y = 0; y < LCD_V_RES; ++y) {
        amoled_set_window(0, y, LCD_H_RES - 1, y);
        amoled_push_buffer(line, LCD_H_RES);
    }
}

void board_init(void)
{
    ESP_LOGI(TAG, "%s init", BOARD_NAME);
    ESP_ERROR_CHECK(init_display());
    // Touch (CST226) not yet integrated via esp_lcd_touch in this repo
}

const char *board_get_name(void)
{
    return BOARD_NAME;
}

bool board_has_lcd(void)
{
    return s_lcd_ready;
}

void board_lcd_sanity_test(void)
{
    if (!s_lcd_ready) {
        ESP_LOGW(TAG, "Panel missing; skip sanity test");
        return;
    }

    // Draw four white corner blocks in logical space and leave on screen
    ESP_LOGI(TAG, "Draw rotated white corner blocks (no fullscreen)");
    uint16_t w = 50, h = 50;
    draw_block_rotated(0, 0, w, h, 0xFFFF);
    draw_block_rotated(LCD_V_RES - w, 0, w, h, 0xFFFF);
    draw_block_rotated(0, LCD_H_RES - h, w, h, 0xFFFF);
    draw_block_rotated(LCD_V_RES - w, LCD_H_RES - h, w, h, 0xFFFF);
}
