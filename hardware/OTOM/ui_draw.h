#pragma once

#include "globals.h"

// =============================
// Drawing helpers
// =============================
static void drawHeader(const char* title) {
  // Bold, inverted header bar (Flipper Zero style)
  display.fillRect(0, 0, 128, 11, 1);
  display.setCursor(2, 2);
  display.setTextSize(1);
  display.setTextColor(0); // Black text on white header
  display.print(title);
  
  // Status indicator area
  if (sdReady) {
    display.setCursor(114, 2);
    display.print("SD");
  }
}

static void drawMenu() {
  display.clearDisplay();
  drawHeader("NEXUS Menu");

  const int y0 = 14;
  const int lineH = 10;

  int start = menuIndex - 2;
  if (start < 0) start = 0;
  if (start > (int)MAIN_COUNT - 4) start = (int)MAIN_COUNT - 4; // Show 4 items max
  if (start < 0) start = 0;

  for (int i = 0; i < 4; i++) {
    int idx = start + i;
    if (idx >= (int)MAIN_COUNT) break;

    int y = y0 + i * lineH;
    bool sel = (idx == menuIndex);

    if (sel) { 
        // Thick selection box with inverted text
        display.fillRect(0, y, 128, lineH, 1); 
        display.setTextColor(0); 
        display.setCursor(4, y + 1);
        display.print("> ");
        display.print(MAIN_ITEMS[idx]);
    } else { 
        display.setTextColor(1); 
        display.setCursor(10, y + 1);
        display.print(MAIN_ITEMS[idx]);
    }
  }

  // Draw scrollbar
  int scrollbarH = 40;
  int thumbH = scrollbarH / MAIN_COUNT;
  if (thumbH < 4) thumbH = 4;
  int thumbY = y0 + (menuIndex * (scrollbarH - thumbH)) / (MAIN_COUNT - 1);
  display.drawLine(126, y0, 126, y0 + scrollbarH, 1);
  display.fillRect(125, thumbY, 3, thumbH, 1);

  display.setTextColor(1);
  display.setCursor(0, 56);
  display.print("Up/Dn:Sel  Ent:Go");
  display.display();
}

static void drawJamMenu() {
  display.clearDisplay();
  drawHeader("Jamming Menu");

  const int y0 = 14;
  const int lineH = 10;

  for (int i = 0; i < JAM_COUNT; i++) {
    int y = y0 + i * lineH;
    bool sel = (i == jamIndex);

    if (sel) { 
        display.fillRect(0, y, 128, lineH, 1); 
        display.setTextColor(0); 
        display.setCursor(4, y + 1);
        display.print("> ");
        display.print(JAM_ITEMS[i]);
    } else { 
        display.setTextColor(1); 
        display.setCursor(10, y + 1);
        display.print(JAM_ITEMS[i]);
    }
  }

  // Draw scrollbar
  int scrollbarH = 40;
  int thumbH = scrollbarH / JAM_COUNT;
  if (thumbH < 4) thumbH = 4;
  int thumbY = y0 + (jamIndex * (scrollbarH - thumbH)) / (JAM_COUNT - 1);
  display.drawLine(126, y0, 126, y0 + scrollbarH, 1);
  display.fillRect(125, thumbY, 3, thumbH, 1);

  display.setTextColor(1);
  display.setCursor(0, 56);
  display.print("Up/Dn:Sel  Ent:Go");
  display.display();
}

static void drawConfirm() {
  display.clearDisplay();
  drawHeader(confirmTitle);
  display.setTextColor(1);
  display.setCursor(0, 18);
  display.print(confirmAction);
  display.setCursor(0, 56);
  display.print(confirmArmed ? "Confirm=START Exit=No" : "Confirm=Arm Exit=No");
  display.display();
}

static void drawStatusPage() {
  display.clearDisplay();
  drawHeader("Status");
  display.setTextColor(1);
  display.setCursor(0, 14); display.print(status.sdMsg);
  display.setCursor(0, 24); display.print(status.n1Msg);
  display.setCursor(0, 34); display.print(status.n2Msg);
  display.setCursor(0, 44); display.print("Signals: "); display.print(capturedCount); display.print("/10");
  display.setCursor(0, 56); display.print("Exit=Back Enter=Rfr");
  display.display();
}

static void drawSpectrumPageIdle() {
  display.clearDisplay();
  drawHeader("Spectrum Scan");
  display.setTextColor(1);
  display.setCursor(0, 18); display.print("Scan 2.4GHz band");
  display.setCursor(0, 28); display.print("Find active channels");
  display.setCursor(0, 42); display.print("Enter: Start");
  display.setCursor(0, 56); display.print("Exit: Back");
  display.display();
}

static void drawLinkTestPageIdle() {
  display.clearDisplay();
  drawHeader("RF Link Test");
  display.setTextColor(1);
  display.setCursor(0, 18); display.print("Test radio comms");
  display.setCursor(0, 28); display.print("Dual-radio test");
  display.setCursor(0, 42); display.print("Enter: Start");
  display.setCursor(0, 56); display.print("Exit: Back");
  display.display();
}

static void drawCapturePageIdle() {
  display.clearDisplay();
  drawHeader("Capture Signal");
  display.setTextColor(1);
  display.setCursor(0, 18); display.print("Listen for RF");
  display.setCursor(0, 28); display.print("Slots: "); display.print(capturedCount); display.print("/10");
  display.setCursor(0, 42); display.print("Enter: Start");
  display.setCursor(0, 56); display.print("Exit: Back");
  display.display();
}

static void drawSignalsPage() {
  display.clearDisplay();
  drawHeader("Saved Signals");
  display.setTextColor(1);
  if (capturedCount == 0) {
    display.setCursor(0, 14); display.print("No signals saved");
    const int y0 = 24;
    const int lineH = 10;
    for (int i = 0; i < (int)SIGNALS_ACTION_COUNT; i++) {
      int y = y0 + i * lineH;
      bool sel = (i == replayIndex);
      if (sel) { display.fillRect(0, y - 1, 128, lineH, 1); display.setTextColor(0); }
      else     { display.setTextColor(1); }
      display.setCursor(2, y);
      display.print(SIGNALS_ACTIONS[i]);
    }
    display.setTextColor(1);
    display.setCursor(0, 56);
    if (replayIndex == 0) display.print("Enter=Save Exit=Back");
    else if (replayIndex == 1) display.print("Enter=Load Exit=Back");
    else display.print("Enter=Clear Exit=Back");
  } else {
    const int y0 = 14;
    const int lineH = 9;
    int total = capturedCount + SIGNALS_ACTION_COUNT;
    int start = replayIndex - 2;
    if (start < 0) start = 0;
    if (start > total - 4) start = total - 4;
    if (start < 0) start = 0;
    for (int i = 0; i < 4; i++) {
      int idx = start + i;
      if (idx >= total) break;
      int y = y0 + i * lineH;
      bool sel = (idx == replayIndex);
      if (sel) { display.fillRect(0, y - 1, 128, lineH, 1); display.setTextColor(0); }
      else     { display.setTextColor(1); }
      display.setCursor(2, y);
      if (idx < (int)capturedCount) {
        display.print(idx); display.print(": CH"); display.print(capturedSignals[idx].channel);
        display.print(" "); display.print(capturedSignals[idx].payloadSize); display.print("B");
      } else {
        display.print(SIGNALS_ACTIONS[idx - capturedCount]);
      }
    }
    display.setTextColor(1);
    display.setCursor(0, 56);
    if (replayIndex < (int)capturedCount) display.print("Enter=Rply Confirm=Del");
    else {
      int action = replayIndex - capturedCount;
      if (action == 0) display.print("Enter=Save Exit=Back");
      else if (action == 1) display.print("Enter=Load Exit=Back");
      else display.print("Enter=Clear Exit=Back");
    }
  }
  display.display();
}

static void drawMonitorPageIdle() {
  display.clearDisplay();
  drawHeader("Monitor Mode");
  display.setTextColor(1);
  display.setCursor(0, 18); display.print("Live RF capture");
  display.setCursor(0, 28); display.print("Real-time packets");
  display.setCursor(0, 42); display.print("Enter: Start");
  display.setCursor(0, 56); display.print("Exit: Back");
  display.display();
}

static void drawSdPageIdle() {
  display.clearDisplay();
  drawHeader("microSD");
  display.setTextColor(1);
  display.setCursor(0, 16); display.print(status.sdMsg);
  display.setCursor(0, 28); display.print("Enter: Remount");
  display.setCursor(0, 38); display.print("Confirm: Bench");
  display.setCursor(0, 56); display.print("Exit=Back");
  display.display();
}

static void drawSettings() {
  display.clearDisplay();
  drawHeader("Settings");
  display.setTextColor(1);
  display.setCursor(0, 16); display.print("Placeholder");
  display.setCursor(0, 56); display.print("Exit=Back");
  display.display();
}

static void drawAbout() {
  display.clearDisplay();
  drawHeader("About");
  display.setTextColor(1);
  display.setCursor(0, 14); display.print("NEXUS RF System");
  display.setCursor(0, 24); display.print("Dual nRF24L01+");
  display.setCursor(0, 34); display.print("Full RF toolkit");
  display.setCursor(0, 56); display.print("Exit=Back");
  display.display();
}

static void drawFilesPage() {
  display.clearDisplay();
  drawHeader("SD Files");
  display.setTextColor(1);
  if (!sdReady) {
    display.setCursor(0, 24); display.print("SD not ready");
    display.setCursor(0, 56); display.print("Enter=Retry Exit=Back");
    display.display();
    return;
  }
  if (fileCount == 0) {
    display.setCursor(0, 24); display.print("No files found");
    display.setCursor(0, 56); display.print("Enter=Rfr Exit=Back");
    display.display();
    return;
  }
  const int y0 = 14;
  const int lineH = 9;
  int start = fileIndex - 2;
  if (start < 0) start = 0;
  if (start > (int)fileCount - 5) start = (int)fileCount - 5;
  if (start < 0) start = 0;
  for (int i = 0; i < 5; i++) {
    int idx = start + i;
    if (idx >= (int)fileCount) break;
    int y = y0 + i * lineH;
    bool sel = (idx == fileIndex);
    if (sel) { display.fillRect(0, y - 1, 128, lineH, 1); display.setTextColor(0); }
    else     { display.setTextColor(1); }
    display.setCursor(2, y);
    display.print(fileNames[idx]);
  }
  display.setTextColor(1);
  display.setCursor(0, 56);
  display.print("Enter=Rfr Exit=Back");
  display.display();
}

static void drawSessionPage() {
  display.clearDisplay();
  drawHeader("Session Log");
  display.setTextColor(1);
  display.setCursor(0, 16); display.print("Status: "); display.print(sessionOn ? "ON" : "OFF");
  if (sessionOn) { display.setCursor(0, 26); display.print("File: "); display.print(sessionPath); }
  display.setCursor(0, 42); display.print(sessionOn ? "Enter: Stop" : "Enter: Start");
  display.setCursor(0, 56); display.print("Exit=Back");
  display.display();
}

static void drawWifiPage() {
  display.clearDisplay();
  drawHeader("Wi-Fi Scan");
  display.setTextColor(1);
  if (!wifiScanned) {
    display.setCursor(0, 24); display.print("Enter: Scan");
    display.setCursor(0, 56); display.print("Exit=Back");
    display.display();
    return;
  }
  if (wifiCount == 0) {
    display.setCursor(0, 24); display.print("No networks");
    display.setCursor(0, 56); display.print("Enter=Rescan Exit=Back");
    display.display();
    return;
  }
  const int y0 = 14;
  const int lineH = 8;
  int lines = wifiCount;
  if (lines > 6) lines = 6;
  for (int i = 0; i < lines; i++) {
    int y = y0 + i * lineH;
    display.setCursor(0, y);
    display.print(wifiNames[i]);
    display.print(" ");
    display.print(wifiRssi[i]);
    display.print("d ");
    display.print("CH");
    display.print(wifiChan[i]);
  }
  display.display();
}

static void drawBlePage() {
  display.clearDisplay();
  drawHeader("BLE Scan");
  display.setTextColor(1);
  display.setCursor(0, 24); display.print("BLE scan requires");
  display.setCursor(0, 34); display.print("BLE library");
  display.setCursor(0, 56); display.print("Exit=Back");
  display.display();
}

static void drawNfcPage() {
  display.clearDisplay();
  drawHeader("NFC");
  display.setTextColor(1);
  display.setCursor(0, 24); display.print("NFC not available");
  display.setCursor(0, 56); display.print("Exit=Back");
  display.display();
}

static void drawBadUsbPage() {
  display.clearDisplay();
  drawHeader("BadUSB");
  display.setTextColor(1);
  display.setCursor(0, 24); display.print("Not configured");
  display.setCursor(0, 56); display.print("Exit=Back");
  display.display();
}

// =============================
// Spectrum drawing
// =============================
static void drawSpectrumRunning() {
  display.clearDisplay();
  drawHeader("Spectrum Scan");
  display.setTextColor(1);

  int pct = (int)((specRep * 100UL) / SPEC_REPS);
  display.setCursor(0, 14); display.print("Scanning...");
  display.setCursor(0, 24); display.print("Pass: "); display.print(specRep); display.print("/"); display.print(SPEC_REPS);
  display.setCursor(0, 34); display.print("Progress: "); display.print(pct); display.print("%");

  int w = (pct * 128) / 100;
  display.drawRect(0, 44, 128, 8, 1);
  display.fillRect(1, 45, w - 2 < 0 ? 0 : w - 2, 6, 1);

  display.setCursor(0, 56); display.print("Exit=Stop");
  display.display();
}

static void drawSpectrumResult() {
  uint8_t topCh[3] = {0,0,0};
  uint8_t topVal[3] = {0,0,0};

  for (uint8_t ch = 0; ch < NUM_CH; ch++) {
    uint8_t v = specVals[ch];
    if (v > topVal[0]) {
      topVal[2]=topVal[1]; topCh[2]=topCh[1];
      topVal[1]=topVal[0]; topCh[1]=topCh[0];
      topVal[0]=v;         topCh[0]=ch;
    } else if (v > topVal[1]) {
      topVal[2]=topVal[1]; topCh[2]=topCh[1];
      topVal[1]=v;         topCh[1]=ch;
    } else if (v > topVal[2]) {
      topVal[2]=v;         topCh[2]=ch;
    }
  }

  display.clearDisplay();
  drawHeader("Spectrum Result");
  display.setTextColor(1);

  display.setCursor(0, 14); display.print("Top channels:");
  for (int i = 0; i < 3; i++) {
    display.setCursor(0, 24 + i*10);
    display.print(i+1);
    display.print(") CH");
    display.print(topCh[i]);
    display.print("  ");
    display.print(topVal[i]);
  }

  display.setCursor(0, 56); display.print("Exit=Back Enter=Again");
  display.display();
}

// =============================
// Link test drawing
// =============================
static void drawLinkRunning() {
  display.clearDisplay();
  drawHeader("RF Link Test");
  display.setTextColor(1);
  display.setCursor(0, 14); display.print("TX: "); display.print(ltTx);
  display.setCursor(0, 24); display.print("RX: "); display.print(ltRx);
  display.setCursor(0, 34);
  if (ltTx) {
    int pct = (ltRx * 100) / ltTx;
    display.print("Success: "); display.print(pct); display.print("%");
  } else {
    display.print("Success: --");
  }
  display.setCursor(0, 56); display.print("Exit=Stop");
  display.display();
}

// =============================
// Capture drawing
// =============================
static void drawCaptureRunning() {
  display.clearDisplay();
  drawHeader("Capturing...");
  display.setTextColor(1);
  display.setCursor(0, 18); display.print("CH: "); display.print(capCh); display.print("/125");
  display.setCursor(0, 28); display.print("Pkts: "); display.print(capPackets);
  display.setCursor(0, 38); display.print("Found: "); display.print(capturedCount); display.print("/10");
  display.setCursor(0, 56); display.print("Exit=Stop");
  display.display();
}

static void drawCaptureResult(bool success) {
  display.clearDisplay();
  drawHeader(success ? "Captured!" : "No Signal");
  display.setTextColor(1);
  
  if (success) {
    CapturedSignal* sig = &capturedSignals[capturedCount - 1];
    display.setCursor(0, 14); display.print("CH: "); display.print(sig->channel);
    display.setCursor(0, 24); 
    display.print("Addr: ");
    for (int i = 0; i < 3; i++) {
      if (sig->address[i] < 0x10) display.print("0");
      display.print(sig->address[i], HEX);
    }
    display.setCursor(0, 34); display.print("Size: "); display.print(sig->payloadSize); display.print("B");
    display.setCursor(0, 44); display.print("Slot: "); display.print(capturedCount - 1);
  } else {
    display.setCursor(0, 24); display.print("No RF detected");
    display.setCursor(0, 34); display.print("Try again");
  }
  
  display.setCursor(0, 56); display.print("Exit=Back");
  display.display();
}

// =============================
// Monitor drawing
// =============================
static void drawMonitorRunning() {
  display.clearDisplay();
  drawHeader("Monitor Mode");
  display.setTextColor(1);
  display.setCursor(0, 18); display.print("CH: "); display.print(monCh);
  display.setCursor(0, 28); display.print("Packets: "); display.print(monPackets);
  display.setCursor(0, 38); display.print("Live capture...");
  display.setCursor(0, 56); display.print("Exit=Stop");
  display.display();
}

// =============================
// Jam drawing
// =============================
static void drawJamRunning(const char* type, const char* detail) {
  display.clearDisplay();
  drawHeader("JAMMING ACTIVE");
  display.setTextColor(1);
  
  display.setCursor(0, 14); 
  display.print("Type: "); display.print(type);
  
  display.setCursor(0, 24); 
  display.print(detail);
  
  uint32_t elapsed = (millis() - jamStart) / 1000;
  display.setCursor(0, 34); 
  display.print("Time: "); display.print(elapsed); display.print("s");
  
  display.setCursor(0, 44); 
  display.print("Hops: "); display.print(jamCount);
  
  display.setCursor(0, 56); 
  display.print("Exit=STOP");
  display.display();
}

// =============================
// Quick message helper
// =============================
static void showQuickMessage(const char* title, const char* line1, const char* line2) {
  display.clearDisplay();
  drawHeader(title);
  display.setTextColor(1);
  if (line1) { display.setCursor(0, 24); display.print(line1); }
  if (line2) { display.setCursor(0, 34); display.print(line2); }
  display.display();
  delay(700);
}
// =============================
// Remote Execution Page
// =============================
static void drawRemotePage() {
  display.clearDisplay();
  drawHeader("NEXUS Remote");
  display.setTextColor(1);
  
  const char* remote_cmds[] = { "Launch Terminal", "Open Calculator", "Go to GitHub", "Ping NEXUS" };
  const int count = 4;
  
  const int y0 = 14;
  const int lineH = 10;

  for (int i = 0; i < count; i++) {
    int y = y0 + i * lineH;
    bool sel = (i == replayIndex); // Reuse replayIndex for menu selection

    if (sel) { display.fillRect(0, y - 1, 128, lineH, 1); display.setTextColor(0); }
    else     { display.setTextColor(1); }

    display.setCursor(2, y);
    display.print(remote_cmds[i]);
  }

  display.setTextColor(1);
  display.setCursor(0, 56);
  display.print("Enter=EX Exit=Back");
  display.display();
}
