#pragma once

#include <Wire.h>
#include <SPI.h>
#include <SD.h>
#include <WiFi.h>

#include <Adafruit_GFX.h>
#include <Adafruit_SH110X.h>
#include <FluxGarage_RoboEyes.h>

#include <RF24.h>

#include "config.h"
#include "types.h"

// =============================
// Display + Eyes
// =============================
Adafruit_SH1106G display(128, 64, &Wire, -1);
RoboEyes<Adafruit_SH1106G> eyes(display);

// =============================
// Radios + SD SPI
// =============================
RF24 radio1(NRF1_CE, NRF1_CSN);
RF24 radio2(NRF2_CE, NRF2_CSN);
SPIClass sdSPI(HSPI);

// =============================
// Jamming Channel Arrays
// =============================
int bluetooth_channels[] = {32, 34, 46, 48, 50, 52, 0, 1, 2, 4, 6, 8, 22, 24, 26, 28, 30, 74, 76, 78, 80};
int ble_channels[] = {2, 26, 80};
const int bt_ch_count = sizeof(bluetooth_channels) / sizeof(bluetooth_channels[0]);
const int ble_ch_count = sizeof(ble_channels) / sizeof(ble_channels[0]);

// =============================
// Signal Storage
// =============================
CapturedSignal capturedSignals[10];
uint8_t capturedCount = 0;
static const char* SIGNALS_PATH = "/signals.bin";
static const uint8_t SIGNALS_MAGIC[4] = {'O','T','O','M'};
static const uint8_t SIGNALS_VERSION = 1;
static const char* SIGNALS_ACTIONS[] = {"Save to SD","Load from SD","Clear All"};
static const uint8_t SIGNALS_ACTION_COUNT = sizeof(SIGNALS_ACTIONS)/sizeof(SIGNALS_ACTIONS[0]);

// Common addresses to scan
const uint8_t commonAddresses[][5] = {
  {0xE7, 0xE7, 0xE7, 0xE7, 0xE7},
  {0xC2, 0xC2, 0xC2, 0xC2, 0xC2},
  {0xE8, 0xE8, 0xE8, 0xE8, 0xE8},
  {0xF0, 0xF0, 0xF0, 0xF0, 0xF0},
  {0x55, 0x55, 0x55, 0x55, 0x55},
  {0xAA, 0xAA, 0xAA, 0xAA, 0xAA},
  {0x00, 0x00, 0x00, 0x00, 0x00},
  {0xFF, 0xFF, 0xFF, 0xFF, 0xFF}
};

// =============================
// Buttons
// =============================
Button bUp      { BTN_UP };
Button bDown    { BTN_DOWN };
Button bEnter   { BTN_ENTER };
Button bExit    { BTN_EXIT };
Button bConfirm { BTN_CONFIRM };

static uint32_t lastActivityMs = 0;

// =============================
// Status
// =============================
Status status;

static bool sdReady  = false;
static bool nrf1Ready = false;
static bool nrf2Ready = false;
static bool sessionOn = false;
static char sessionPath[32] = "";

// =============================
// UI state
// =============================
UiMode uiMode = UI_MENU;
PageId page   = PAGE_NONE;
SubMenuId subMenu = SUB_NONE;
RunMode runMode = RUN_NONE;

static const char* MAIN_ITEMS[] = {
  "Status",
  "Spectrum Scan",
  "RF Link Test",
  "Capture Signal",
  "List Signals",
  "Monitor Mode",
  "Jamming Menu",
  "microSD",
  "Settings",
  "About",
  "SD Files",
  "Session Log",
  "Wi-Fi Scan",
  "BLE Scan",
  "NFC",
  "BadUSB",
  "NEXUS Remote",
  "Play DOOM!"
};
static const uint8_t MAIN_COUNT = sizeof(MAIN_ITEMS)/sizeof(MAIN_ITEMS[0]);
static int menuIndex = 0;

static const char* JAM_ITEMS[] = {
  "Jam Bluetooth",
  "Jam BLE",
  "Jam ALL (BT+BLE)",
  "Custom Channel"
};
static const uint8_t JAM_COUNT = sizeof(JAM_ITEMS)/sizeof(JAM_ITEMS[0]);
static int jamIndex = 0;
static char fileNames[32][24];
static uint8_t fileCount = 0;
static int fileIndex = 0;
static bool wifiScanned = false;
static uint8_t wifiCount = 0;
static char wifiNames[6][20];
static int8_t wifiRssi[6];
static uint8_t wifiChan[6];

// Replay signal selection
static int replayIndex = 0;

// Confirm (double-confirm)
static const char* confirmTitle  = "Confirm?";
static const char* confirmAction = "";
static void (*confirmCallback)() = nullptr;
static bool confirmArmed = false;
static uint32_t confirmArmMs = 0;
static UiMode confirmReturnMode = UI_MENU;
static PageId confirmReturnPage = PAGE_NONE;
static SubMenuId confirmReturnSub = SUB_NONE;
static int confirmReturnMenuIndex = 0;
static int confirmReturnJamIndex = 0;
static int confirmReturnReplayIndex = 0;
static int pendingSignalIndex = -1;

// =============================
// Telemetry Output
// =============================
#ifndef NEXUS_WIFI_SSID
#define NEXUS_WIFI_SSID ""
#endif

#ifndef NEXUS_WIFI_PASS
#define NEXUS_WIFI_PASS ""
#endif

static const uint32_t TELEMETRY_HEARTBEAT_MS = 2000;
static const uint16_t TELEMETRY_TCP_PORT = 9000;
static WiFiServer telemetryServer(TELEMETRY_TCP_PORT);
static WiFiClient telemetryClients[3];
static bool telemetryTcpStarted = false;
static uint32_t telemetrySeq = 0;
static uint32_t telemetryLastHeartbeat = 0;
static char telemetryDeviceId[24] = "OTOM-UNKNOWN";

// =============================
// Spectrum scan state
// =============================
static const uint8_t NUM_CH = 126;
static uint8_t specVals[NUM_CH];
static uint16_t specRep = 0;
static uint8_t  specChA = 0;
static uint8_t  specChB = 63;
static const uint16_t SPEC_REPS = 80;
static bool specDone = false;

// =============================
// Link test state
// =============================
static const uint8_t ADDR_A[5] = {'N','X','A','A','A'};
static const uint8_t ADDR_B[5] = {'N','X','B','B','B'};
static uint16_t ltTx = 0, ltRx = 0;
static uint32_t ltLastMs = 0;
static uint8_t  ltState = 0;
static uint32_t ltDeadline = 0;

// =============================
// Capture state
// =============================
static uint16_t capPackets = 0;
static uint8_t capCh = 0;
static uint8_t capAddr = 0;

// =============================
// Monitor state
// =============================
static uint16_t monPackets = 0;
static uint8_t monCh = 0;
static uint8_t monAddr = 0;

// =============================
// Jam state
// =============================
static uint32_t jamCount = 0;
static uint32_t jamStart = 0;
