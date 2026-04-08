#pragma once

// =============================
// Pins (NEXUS Configuration)
// =============================

// OLED I2C
#define SDA_PIN     8
#define SCL_PIN     9
#define OLED_ADDR   0x3C

// SPI BUS #1 (nRF24 shared bus)
#define NRF_SPI_SCK   12
#define NRF_SPI_MOSI  11
#define NRF_SPI_MISO  13

// SPI BUS #2 (microSD dedicated bus)
#define SD_SPI_SCK    15
#define SD_SPI_MOSI   1
#define SD_SPI_MISO   2
#define SD_CS         10

// nRF24L01 #1
#define NRF1_CE       4
#define NRF1_CSN      5

// nRF24L01 #2
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
