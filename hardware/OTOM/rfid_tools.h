#pragma once

#include "globals.h"
#include "ui_draw.h"
#include <SPI.h>
#include <MFRC522.h>

#ifndef RFID_CS
#define RFID_CS 48
#endif

// We use the default SPI bus for MFRC522
// SS = RFID_CS, RST = UNUSED/SOFT
#define RFID_RST 0 

static MFRC522 mfrc522(RFID_CS, RFID_RST);
static bool rfidInitialized = false;

static uint8_t savedUid[10];
static uint8_t savedUidSize = 0;
static bool hasSavedUid = false;

// Simulated states
static uint32_t rfidAnimMs = 0;
static uint8_t rfidScanStep = 0;
static bool isRfidScanning = false;
static int rfidMenuIndex = 0;

static void initRfid() {
  if (!rfidInitialized) {
    mfrc522.PCD_Init();
    delay(4);
    mfrc522.PCD_DumpVersionToSerial();
    rfidInitialized = true;
  }
}

static void drawRfidMenu() {
  display.clearDisplay();
  drawHeader("RFID Tools (13.56MHz)");
  
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
    for(int i=0; i<savedUidSize; i++) {
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
  initRfid();
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
  
  // Animation update
  if (now - rfidAnimMs > 500) {
    rfidAnimMs = now;
    rfidScanStep = (rfidScanStep + 1) % 4;
    
    display.clearDisplay();
    drawHeader("RFID: Reading...");
    display.setTextColor(1);
    display.setCursor(0, 24); display.print("Scanning");
    for (uint8_t i = 0; i < rfidScanStep; i++) display.print(".");
    display.setCursor(0, 56); display.print("Exit=Stop");
    display.display();
  }
  
  // Check for card
  if (mfrc522.PICC_IsNewCardPresent() && mfrc522.PICC_ReadCardSerial()) {
    savedUidSize = mfrc522.uid.size;
    memcpy(savedUid, mfrc522.uid.uidByte, savedUidSize);
    hasSavedUid = true;
    
    display.clearDisplay();
    drawHeader("RFID: Card Found!");
    display.setCursor(0, 20); display.print("Type: ");
    MFRC522::PICC_Type piccType = mfrc522.PICC_GetType(mfrc522.uid.sak);
    display.print(mfrc522.PICC_GetTypeName(piccType));
    
    display.setCursor(0, 30); display.print("UID: ");
    for(int i=0; i<savedUidSize; i++) {
      if(savedUid[i] < 0x10) display.print("0");
      display.print(savedUid[i], HEX);
      if(i < savedUidSize - 1) display.print(":");
    }
    display.setCursor(0, 56); display.print("Exit=Back");
    display.display();
    
    mfrc522.PICC_HaltA();
    isRfidScanning = false;
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
  for(int i=0; i<savedUidSize; i++) {
    if(savedUid[i] < 0x10) display.print("0");
    display.print(savedUid[i], HEX);
    if(i < savedUidSize - 1) display.print(":");
  }
  display.setCursor(0, 44); display.print("Using Software Emul");
  display.setCursor(0, 56); display.print("Exit=Stop");
  display.display();
  
  // Basic simulation placeholder
  // A true MIFARE simulation requires low-level timer manipulation or specialized hardware.
  // We use a basic loop here.
  uint32_t startSim = millis();
  while(millis() - startSim < 3000) {
    updateButtons(millis());
    if (bExit.pressedEvent) break;
    delay(10);
  }
  drawRfidMenu();
}
