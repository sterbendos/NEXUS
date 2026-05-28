#pragma once

// =============================
// Pins (NEXUS Configuration)
// =============================

// OLED I2C
#define SDA_PIN     8
#define SCL_PIN     9
#define OLED_ADDR   0x3C

// SPI BUS #1 - FSPI (default SPI)
// Used by: nRF24 #1 + RFID (MFRC522)
#define NRF_SPI_SCK   12
#define NRF_SPI_MOSI  11
#define NRF_SPI_MISO  13
#define RFID_CS       48

// SPI BUS #2 - HSPI (sdSPI)
// Used by: microSD + nRF24 #2 (shared bus, separate CS pins)
#define SD_SPI_SCK    15
#define SD_SPI_MOSI   1
#define SD_SPI_MISO   2
#define SD_CS         10

// nRF24L01 #1  (on FSPI bus — pins 11/12/13)
#define NRF1_CE       4
#define NRF1_CSN      5

// nRF24L01 #2  (on HSPI bus — pins 1/2/15 — MOVE THESE WIRES!)
// SCK  -> GPIO 15   (was 12)
// MOSI -> GPIO 1    (was 11)
// MISO -> GPIO 2    (was 13)
// CE   -> GPIO 7    (no change)
// CSN  -> GPIO 14   (no change)
#define NRF2_CE       7
#define NRF2_CSN      14

// Buttons (INPUT_PULLUP -> pressed = LOW)
#define BTN_UP        16
#define BTN_DOWN      17
#define BTN_ENTER     18
#define BTN_EXIT      21
#define BTN_CONFIRM   47

// =============================
// Timing
// =============================
static const uint32_t IDLE_TIMEOUT_MS = 30000;
static const uint32_t DEBOUNCE_MS     = 25;
