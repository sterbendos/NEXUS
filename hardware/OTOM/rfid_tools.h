#pragma once

#include "globals.h"
#include "ui_draw.h"

// ==========================================
// RFID / NFC Tool (FlipperZero-like concept)
// ==========================================
// Requires an MFRC522 module on the main SPI bus.
// Since original pinouts are hard-wired, we define a soft CS pin here
// that users can wire to an MFRC522 SDA/CS pin (e.g., Pin 48 on ESP32-S3).
#ifndef RFID_CS
#define RFID_CS 48
#endif

// Placeholder UID storage
static uint8_t savedUid[4] = {0xDE, 0xAD, 0xBE, 0xEF};
static bool hasSavedUid = false;

// Simulated states
static uint32_t rfidAnimMs = 0;
static uint8_t rfidScanStep = 0;
static bool isRfidScanning = false;
static int rfidMenuIndex = 0;

static void drawRfidMenu() {
  display.clearDisplay();
  drawHeader("RFID Tools (125kHz)");
  
  const char* items[] = {"1. Read Card", "2. Emulate Saved"};
  for (int i = 0; i < 2; i++) {
    int y = 14 + i * 10;
    if (i == rfidMenuIndex) {
      display.fillRect(0, y - 1, 128, 10, 1);
      display.setTextColor(0);
    } else {
      display.setTextColor(1);
    }
    display.setCursor(2, y);
    display.print(items[i]);
  }
  
  display.setTextColor(1);
  display.setCursor(0, 36); display.print("Status: ");
  if (hasSavedUid) {
    for(int i=0; i<4; i++) {
      if(savedUid[i] < 0x10) display.print("0");
      display.print(savedUid[i], HEX);
    }
  } else {
    display.print("Empty");
  }
  
  display.setCursor(0, 56); display.print("Up/Dn Enter Exit");
  display.display();
}

static void startRfidRead() {
  isRfidScanning = true;
  rfidAnimMs = millis();
  rfidScanStep = 0;
  
  display.clearDisplay();
  drawHeader("RFID: Reading...");
  display.setTextColor(1);
  display.setCursor(0, 24); display.print("Hold card to reader");
  display.setCursor(0, 56); display.print("Exit=Stop");
  display.display();
}

static void rfidReadStep() {
  uint32_t now = millis();
  if (now - rfidAnimMs > 500) {
    rfidAnimMs = now;
    rfidScanStep = (rfidScanStep + 1) % 4;
    
    display.clearDisplay();
    drawHeader("RFID: Reading...");
    display.setTextColor(1);
    display.setCursor(0, 24); display.print("Scanning");
    for (uint8_t i = 0; i < rfidScanStep; i++) display.print(".");
    
    // Simulate finding a card after ~2 seconds
    if (random(0, 10) > 8 && rfidScanStep > 1) {
      savedUid[0] = random(0, 255);
      savedUid[1] = random(0, 255);
      savedUid[2] = random(0, 255);
      savedUid[3] = random(0, 255);
      hasSavedUid = true;
      
      display.clearDisplay();
      drawHeader("RFID: Card Found!");
      display.setCursor(0, 20); display.print("Type: MIFARE 1K");
      display.setCursor(0, 30); display.print("UID: ");
      for(int i=0; i<4; i++) {
        if(savedUid[i] < 0x10) display.print("0");
        display.print(savedUid[i], HEX);
        if(i<3) display.print(":");
      }
      display.setCursor(0, 56); display.print("Exit=Back");
      display.display();
      isRfidScanning = false; // Stop scanning
      return;
    }
    
    display.setCursor(0, 56); display.print("Exit=Stop");
    display.display();
  }
}

static void startRfidSimulate() {
  if (!hasSavedUid) {
    showQuickMessage("RFID Sim", "No UID saved!", "Read a card first");
    drawRfidMenu();
    return;
  }
  
  display.clearDisplay();
  drawHeader("RFID: Emulating");
  display.setTextColor(1);
  display.setCursor(0, 20); display.print("Broadcasting UID:");
  display.setCursor(0, 30); 
  for(int i=0; i<4; i++) {
    if(savedUid[i] < 0x10) display.print("0");
    display.print(savedUid[i], HEX);
    if(i<3) display.print(":");
  }
  display.setCursor(0, 44); display.print("Reader must support it");
  display.setCursor(0, 56); display.print("Exit=Stop");
  display.display();
  
  // Flipper Zero uses GPIO toggling on the antenna to simulate tags.
  // We leave this as a stub for actual MFRC522 or antenna driver injection.
}
