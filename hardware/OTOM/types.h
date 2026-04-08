#pragma once

#include <Arduino.h>

// =============================
// UI types
// =============================
enum UiMode { UI_MENU, UI_PAGE, UI_IDLE_EYES, UI_CONFIRM, UI_SUBMENU };
enum PageId { PAGE_NONE, PAGE_STATUS, PAGE_SPECTRUM, PAGE_LINKTEST, PAGE_SD, PAGE_SETTINGS, PAGE_ABOUT, 
              PAGE_CAPTURE, PAGE_SIGNALS, PAGE_REPLAY, PAGE_MONITOR, PAGE_JAM, PAGE_FILES, PAGE_SESSION, 
              PAGE_WIFI, PAGE_BLE, PAGE_NFC, PAGE_BADUSB, PAGE_DOOM, PAGE_REMOTE };
enum SubMenuId { SUB_NONE, SUB_JAM };

enum RunMode { RUN_NONE, RUN_SPECTRUM, RUN_LINKTEST, RUN_SDBENCH, RUN_CAPTURE, RUN_MONITOR, 
               RUN_JAM_BT, RUN_JAM_BLE, RUN_JAM_ALL, RUN_JAM_CUSTOM, RUN_DOOM, RUN_WIFI_ATTACK, RUN_BLE_SPAM };

// =============================
// Captured Signals Storage
// =============================
struct CapturedSignal {
  uint8_t channel;
  uint8_t address[5];
  uint8_t payload[32];
  uint8_t payloadSize;
  bool isValid;
};

struct SignalFileHeader {
  uint8_t magic[4];
  uint8_t version;
  uint8_t count;
  uint8_t reserved[2];
};

struct SignalFileRecord {
  uint8_t channel;
  uint8_t address[5];
  uint8_t payloadSize;
  uint8_t payload[32];
};

// =============================
// Buttons (robust debounce)
// =============================
struct Button {
  uint8_t pin;
  bool stable = HIGH;
  bool rawLast = HIGH;
  uint32_t lastEdge = 0;
  bool pressedEvent = false;
};

// =============================
// Status
// =============================
struct Status {
  bool sdOk = false;
  bool nrf1Ok = false;
  bool nrf2Ok = false;
  char sdMsg[24]  = "SD: ?";
  char n1Msg[24]  = "NRF1: ?";
  char n2Msg[24]  = "NRF2: ?";
};
