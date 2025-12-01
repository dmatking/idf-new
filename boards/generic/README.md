# Generic ESP32  

A quick test of *idf.py build flash monitor* for an ESP32. Technically this should work for any ESP32, that can be flashed from UART. It sets up a FreeRTOS task, starts it and outputs to the serial console every second. 

---

### ESP-IDF Notes

 - ESP-IDF > 5.5.1

---

### Expected Output

    I (267) main_task: Started on CPU0
    I (277) main_task: Calling app_main()
    I (277) APP: app_main starting
    I (277) BOARD_GENERIC: Generic ESP32 board init (no LCD).
    I (277) APP: Board has no LCD configured.
    I (277) APP: Heartbeat starting, period=1000 ms
    I (287) APP: Heartbeat run #1 (board: Generic ESP32)
    I (287) main_task: Returned from app_main()
    I (1277) APP: Heartbeat run #2 (board: Generic ESP32)
    I (2277) APP: Heartbeat run #3 (board: Generic ESP32)
    I (3277) APP: Heartbeat run #4 (board: Generic ESP32)
    I (4277) APP: Heartbeat run #5 (board: Generic ESP32)
    I (5277) APP: Heartbeat run #6 (board: Generic ESP32)
    I (6277) APP: Heartbeat run #7 (board: Generic ESP32)
    I (7277) APP: Heartbeat run #8 (board: Generic ESP32)
    I (8277) APP: Heartbeat run #9 (board: Generic ESP32)
    I (9277) APP: Heartbeat run #10 (board: Generic ESP32)



