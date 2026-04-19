// main_sim.c — desktop sim entry point for __PROJECT_NAME__.
//
// Interactive:  ./sim_build/__PROJECT_NAME___sim
//   P = save screenshot_NNNN.png   Esc/close = quit
//
// Headless:     ./__PROJECT_NAME___sim --screenshot out.png [--frames N]
//   --frames 1 = first frame, --frames 2 = second frame, etc.

#include <SDL2/SDL.h>
#include "board_interface.h"
#include "screencap.h"

int   sim_argc;
char **sim_argv;

int main(int argc, char **argv)
{
    sim_argc = argc;
    sim_argv = argv;

    board_init();

    // Draw a gradient across the full display as a basic smoke test.
    // Replace this with your actual app rendering once you have it.
    int w = board_lcd_width(), h = board_lcd_height();
    for (int y = 0; y < h; y++) {
        for (int x = 0; x < w; x++) {
            board_lcd_set_pixel_rgb(x, y,
                (uint8_t)(x * 255 / (w - 1)),
                (uint8_t)(y * 255 / (h - 1)),
                0x40);
        }
    }
    board_lcd_flush();

    while (screencap_poll())
        SDL_Delay(16);

    screencap_destroy();
    return 0;
}
