cmake_minimum_required(VERSION 3.16)
project(__PROJECT_NAME___sim C)

include(screencap/cmake/screencap.cmake)

screencap_add_sim(__PROJECT_NAME___sim
    SOURCES
        main_sim.c
        ${SCREENCAP_BOARD_INTERFACE_SIM}
    INCLUDES
        ../main
    BOARD_WIDTH  __BOARD_WIDTH__
    BOARD_HEIGHT __BOARD_HEIGHT__
)
