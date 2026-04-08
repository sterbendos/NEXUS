#pragma once

#include "globals.h"
#include "telemetry.h"
#include "ui_draw.h"
#include "rf_tools.h"

// =============================
// TOOL 6: Jamming Functions
// =============================

// Jam Bluetooth Classic (Fast Sweep HIZMOS Style)
static int bt_sweep_idx = 0;

static void startJamBT() {
  jamCount = 0;
  jamStart = millis();
  bt_sweep_idx = 0;
  
  configureRadioForJam(radio1, bluetooth_channels[0]);
  configureRadioForJam(radio2, bluetooth_channels[bt_ch_count / 2]);
  
  runMode = RUN_JAM_BT;
  logEvent("Jam BT start (Sweeping)");
  drawJamRunning("Bluetooth", "Sweeping 79 CH");
}

static void jamBTStep() {
  // HIZMOS high-speed sweep: no delays, continuous carrier switching
  // Radio 1 covers first half, Radio 2 covers second half
  int c1 = bluetooth_channels[bt_sweep_idx % (bt_ch_count / 2)];
  int c2 = bluetooth_channels[(bt_ch_count / 2) + (bt_sweep_idx % (bt_ch_count - (bt_ch_count / 2)))];
  
  radio1.setChannel(c1);
  radio2.setChannel(c2);
  
  bt_sweep_idx++;
  jamCount += 2; // Two channels jammed per tick
  
  if (jamCount % 2000 == 0) {
    char detail[32];
    snprintf(detail, sizeof(detail), "Sweep C1:%d C2:%d", c1, c2);
    drawJamRunning("Bluetooth", detail);
  }
}

// Jam BLE (Fast Advertisement Channel Toggling)
static void startJamBLE() {
  jamCount = 0;
  jamStart = millis();
  
  // BLE primary adv channels: 37 (RF CH 2), 38 (RF CH 26), 39 (RF CH 80)
  configureRadioForJam(radio1, ble_channels[0]); // CH2
  configureRadioForJam(radio2, ble_channels[2]); // CH80
  
  runMode = RUN_JAM_BLE;
  logEvent("Jam BLE start (Aggressive)");
  drawJamRunning("BLE", "Adv Channels");
}

static void jamBLEStep() {
  // Extremely rapid toggling between 2, 26, 80
  // R1 hops 2 and 26. R2 locks 80, occasionally sweeping data channels
  int r1_ch = (jamCount & 1) ? ble_channels[0] : ble_channels[1];
  radio1.setChannel(r1_ch);
  
  if (jamCount % 100 == 0) {
     radio2.setChannel(ble_channels[2]); // Keep resetting to 80 to ensure lock
  }
  
  jamCount++;
  
  if (jamCount % 2000 == 0) {
    drawJamRunning("BLE", "CH 2/26/80 Blitz");
  }
}

// Jam ALL (BT + BLE Full Spectrum Sweep)
static void startJamALL() {
  jamCount = 0;
  jamStart = millis();
  
  configureRadioForJam(radio1, 0);
  configureRadioForJam(radio2, 40);
  
  runMode = RUN_JAM_ALL;
  logEvent("Jam ALL start (Full Sweep)");
  drawJamRunning("ALL (2.4Ghz)", "Full Sweep 0-83");
}

static void jamALLStep() {
  // Linear sweep across entire 2.4GHz band (CH 0 to 83)
  // R1 sweeps 0-41, R2 sweeps 42-83
  int c1 = jamCount % 42;
  int c2 = 42 + (jamCount % 42);
  
  radio1.setChannel(c1);
  radio2.setChannel(c2);
  
  jamCount++;
  
  if (jamCount % 2000 == 0) {
    char detail[32];
    snprintf(detail, sizeof(detail), "Sweep: %d & %d", c1, c2);
    drawJamRunning("ALL (2.4Ghz)", detail);
  }
}

// Custom Channel Jamming (default CH40 + CH80)
static void startJamCustom() {
  jamCount = 0;
  jamStart = millis();
  
  // Default custom channels
  int ch1 = 40;
  int ch2 = 80;
  
  configureRadioForJam(radio1, ch1);
  configureRadioForJam(radio2, ch2);
  
  runMode = RUN_JAM_CUSTOM;
  logEvent("Jam custom start");
  drawJamRunning("Custom", "CH40 + CH80");
}

static void jamCustomStep() {
  jamCount++;
  
  if (jamCount % 100 == 0) {
    drawJamRunning("Custom", "Continuous");
  }
  
  delay(10);
}
