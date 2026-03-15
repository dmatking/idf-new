// Copyright 2025 David M. King
// SPDX-License-Identifier: Apache-2.0

// PDM microphone input
// I2S pins: SCK=IO15, WS=IO2, SD=IO39

#include "mic.h"
#include "driver/i2s_pdm.h"
#include "esp_log.h"

static const char *TAG = "MIC";

#define I2S_PORT        I2S_NUM_1
#define I2S_PIN_SCK     15
#define I2S_PIN_WS      2
#define I2S_PIN_DIN     39

#define SAMPLE_RATE     CONFIG_MIC_SAMPLE_RATE

static i2s_chan_handle_t rx_handle = NULL;

esp_err_t mic_init(void)
{
    i2s_chan_config_t chan_cfg = I2S_CHANNEL_DEFAULT_CONFIG(I2S_PORT, I2S_ROLE_MASTER);
    esp_err_t ret = i2s_new_channel(&chan_cfg, NULL, &rx_handle);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "i2s_new_channel failed: %s", esp_err_to_name(ret));
        return ret;
    }

    i2s_pdm_rx_config_t pdm_cfg = {
        .clk_cfg  = I2S_PDM_RX_CLK_DEFAULT_CONFIG(SAMPLE_RATE),
        .slot_cfg = I2S_PDM_RX_SLOT_DEFAULT_CONFIG(I2S_DATA_BIT_WIDTH_16BIT, I2S_SLOT_MODE_MONO),
        .gpio_cfg = {
            .clk = I2S_PIN_SCK,
            .din = I2S_PIN_DIN,
            .invert_flags = {
                .clk_inv = false,
            },
        },
    };

    ret = i2s_channel_init_pdm_rx_mode(rx_handle, &pdm_cfg);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "i2s_channel_init_pdm_rx_mode failed: %s", esp_err_to_name(ret));
        i2s_del_channel(rx_handle);
        rx_handle = NULL;
        return ret;
    }

    ret = i2s_channel_enable(rx_handle);
    if (ret != ESP_OK) {
        ESP_LOGE(TAG, "i2s_channel_enable failed: %s", esp_err_to_name(ret));
        i2s_del_channel(rx_handle);
        rx_handle = NULL;
        return ret;
    }

    ESP_LOGI(TAG, "Microphone ready (%dHz)", SAMPLE_RATE);
    return ESP_OK;
}

esp_err_t mic_read(int16_t *samples, size_t num_samples, size_t *read_count)
{
    if (!rx_handle) return ESP_ERR_INVALID_STATE;
    size_t bytes_read = 0;
    esp_err_t ret = i2s_channel_read(rx_handle, samples, num_samples * sizeof(int16_t),
                                     &bytes_read, portMAX_DELAY);
    if (read_count) *read_count = bytes_read / sizeof(int16_t);
    return ret;
}
