#pragma once

#include "globals.h"
#include "telemetry.h"
#include "ui_draw.h"

// =============================
// SD mount
// =============================
static bool mountSd() {
  SD.end();
  return SD.begin(SD_CS, sdSPI, 25000000);
}

// =============================
// Status refresh
// =============================
static void refreshStatus() {
  if (!sdReady) sdReady = mountSd();
  status.sdOk = sdReady;
  snprintf(status.sdMsg, sizeof(status.sdMsg), sdReady ? "SD: OK" : "SD: NOT READY");

  if (!nrf1Ready) nrf1Ready = radio1.begin();
  bool ok1 = nrf1Ready && radio1.isChipConnected();
  status.nrf1Ok = ok1;
  snprintf(status.n1Msg, sizeof(status.n1Msg), ok1 ? "NRF1: OK" : "NRF1: FAIL");

  if (!nrf2Ready) nrf2Ready = radio2.begin();
  bool ok2 = nrf2Ready && radio2.isChipConnected();
  status.nrf2Ok = ok2;
  snprintf(status.n2Msg, sizeof(status.n2Msg), ok2 ? "NRF2: OK" : "NRF2: FAIL");
}

// =============================
// Signal management
// =============================
static void deleteSignalAt(uint8_t idx) {
  if (idx >= capturedCount) return;
  for (uint8_t i = idx; i + 1 < capturedCount; i++) capturedSignals[i] = capturedSignals[i + 1];
  capturedCount--;
  if (capturedCount < 10) memset(&capturedSignals[capturedCount], 0, sizeof(CapturedSignal));
}

static void clearAllSignals() {
  memset(capturedSignals, 0, sizeof(capturedSignals));
  capturedCount = 0;
}

static bool saveSignalsToSd() {
  if (!sdReady) sdReady = mountSd();
  if (!sdReady) return false;
  SD.remove(SIGNALS_PATH);
  File f = SD.open(SIGNALS_PATH, FILE_WRITE);
  if (!f) return false;
  SignalFileHeader h;
  memcpy(h.magic, SIGNALS_MAGIC, 4);
  h.version = SIGNALS_VERSION;
  h.count = capturedCount;
  h.reserved[0] = 0;
  h.reserved[1] = 0;
  if (f.write((uint8_t*)&h, sizeof(h)) != sizeof(h)) { f.close(); return false; }
  for (uint8_t i = 0; i < capturedCount; i++) {
    SignalFileRecord r;
    r.channel = capturedSignals[i].channel;
    memcpy(r.address, capturedSignals[i].address, 5);
    r.payloadSize = capturedSignals[i].payloadSize;
    if (r.payloadSize > 32) r.payloadSize = 32;
    memset(r.payload, 0, sizeof(r.payload));
    memcpy(r.payload, capturedSignals[i].payload, r.payloadSize);
    if (f.write((uint8_t*)&r, sizeof(r)) != sizeof(r)) { f.close(); return false; }
  }
  f.flush();
  f.close();
  return true;
}

static bool loadSignalsFromSd() {
  if (!sdReady) sdReady = mountSd();
  if (!sdReady) return false;
  File f = SD.open(SIGNALS_PATH, FILE_READ);
  if (!f) return false;
  SignalFileHeader h;
  if (f.read((uint8_t*)&h, sizeof(h)) != sizeof(h)) { f.close(); return false; }
  if (memcmp(h.magic, SIGNALS_MAGIC, 4) != 0 || h.version != SIGNALS_VERSION) { f.close(); return false; }
  uint8_t count = h.count;
  if (count > 10) count = 10;
  memset(capturedSignals, 0, sizeof(capturedSignals));
  uint8_t actual = 0;
  for (uint8_t i = 0; i < count; i++) {
    SignalFileRecord r;
    if (f.read((uint8_t*)&r, sizeof(r)) != sizeof(r)) break;
    capturedSignals[i].channel = r.channel;
    memcpy(capturedSignals[i].address, r.address, 5);
    capturedSignals[i].payloadSize = r.payloadSize > 32 ? 32 : r.payloadSize;
    memcpy(capturedSignals[i].payload, r.payload, capturedSignals[i].payloadSize);
    capturedSignals[i].isValid = true;
    actual++;
  }
  capturedCount = actual;
  f.close();
  return true;
}

// =============================
// File listing
// =============================
static void refreshFileList() {
  if (!sdReady) { fileCount = 0; fileIndex = 0; return; }
  int prevIndex = fileIndex;
  fileCount = 0;
  File root = SD.open("/");
  if (!root) { fileIndex = 0; return; }
  File entry = root.openNextFile();
  while (entry && fileCount < 32) {
    const char* name = entry.name();
    if (!name) name = "";
    strncpy(fileNames[fileCount], name, sizeof(fileNames[fileCount]) - 1);
    fileNames[fileCount][sizeof(fileNames[fileCount]) - 1] = 0;
    fileCount++;
    entry.close();
    entry = root.openNextFile();
  }
  root.close();
  if (fileCount == 0) fileIndex = 0;
  else {
    if (prevIndex < 0) prevIndex = 0;
    if (prevIndex >= (int)fileCount) prevIndex = fileCount - 1;
    fileIndex = prevIndex;
  }
}

// =============================
// Wi-Fi scan
// =============================
static void wifiScan() {
  wifiScanned = false;
  wifiCount = 0;
  display.clearDisplay();
  drawHeader("Wi-Fi Scan");
  display.setTextColor(1);
  display.setCursor(0, 24); display.print("Scanning...");
  display.display();
  WiFi.mode(WIFI_STA);
  WiFi.disconnect(true);
  delay(100);
  int n = WiFi.scanNetworks();
  if (n < 0) n = 0;
  int limit = n;
  if (limit > 6) limit = 6;
  for (int i = 0; i < limit; i++) {
    String s = WiFi.SSID(i);
    if (s.length() == 0) s = "<hidden>";
    s.toCharArray(wifiNames[i], 13);
    wifiRssi[i] = (int8_t)WiFi.RSSI(i);
    wifiChan[i] = (uint8_t)WiFi.channel(i);
  }
  wifiCount = limit;
  wifiScanned = true;
  WiFi.scanDelete();

  if (NEXUS_WIFI_SSID[0] != '\0') {
    WiFi.begin(NEXUS_WIFI_SSID, NEXUS_WIFI_PASS);
    uint32_t t0 = millis();
    while (WiFi.status() != WL_CONNECTED && (millis() - t0) < 2000) {
      delay(25);
    }
  }
  telemetryTryStartTcpServer();

  char msg[40];
  snprintf(msg, sizeof(msg), "Wi-Fi scan networks=%u", (unsigned)wifiCount);
  logEvent(msg);
  drawWifiPage();
}

// =============================
// Session log
// =============================
static void startSession() {
  if (!sdReady) sdReady = mountSd();
  if (!sdReady) {
    showQuickMessage("Session", "SD not ready", "");
    uiMode = UI_PAGE;
    page = PAGE_SESSION;
    drawSessionPage();
    return;
  }
  if (!SD.exists("/sessions")) SD.mkdir("/sessions");
  uint32_t sid = millis();
  for (uint8_t i = 0; i < 20; i++) {
    snprintf(sessionPath, sizeof(sessionPath), "/sessions/s_%08lu.txt", (unsigned long)(sid + i));
    if (!SD.exists(sessionPath)) break;
  }
  File f = SD.open(sessionPath, FILE_WRITE);
  if (!f) {
    sessionOn = false;
    sessionPath[0] = 0;
    showQuickMessage("Session", "Open failed", "");
    uiMode = UI_PAGE;
    page = PAGE_SESSION;
    drawSessionPage();
    return;
  }
  f.println("OTOM SESSION");
  f.print("START "); f.println(millis());
  f.close();
  sessionOn = true;
  logEvent("Session start");
  uiMode = UI_PAGE;
  page = PAGE_SESSION;
  drawSessionPage();
}

static void stopSession() {
  if (sessionOn && sdReady && sessionPath[0]) {
    File f = SD.open(sessionPath, FILE_WRITE);
    if (f) {
      f.print("STOP "); f.println(millis());
      f.close();
    }
  }
  sessionOn = false;
  logEvent("Session stop");
  uiMode = UI_PAGE;
  page = PAGE_SESSION;
  drawSessionPage();
}

// =============================
// SD Benchmark
// =============================
static void runSdBenchOnce() {
  if (!sdReady) sdReady = mountSd();
  logEvent("SD bench");

  display.clearDisplay();
  drawHeader("SD Bench");
  display.setTextColor(1);
  display.setCursor(0, 18);
  display.print(sdReady ? "Running..." : "SD not ready");
  display.display();
  if (!sdReady) return;

  const char* path = "/bench.bin";
  const size_t BUF_SZ = 4096;
  static uint8_t buf[BUF_SZ];
  for (size_t i = 0; i < BUF_SZ; i++) buf[i] = (uint8_t)(i & 0xFF);
  
  uint32_t t0 = millis();
  File f = SD.open(path, FILE_WRITE);
  if (!f) {
    display.setCursor(0, 32); display.print("Open fail");
    display.display();
    return;
  }
  size_t w = f.write(buf, BUF_SZ);
  f.flush();
  f.close();
  uint32_t t1 = millis();

  f = SD.open(path, FILE_READ);
  if (!f) {
    display.setCursor(0, 32); display.print("Read open fail");
    display.display();
    return;
  }
  size_t r = f.read(buf, BUF_SZ);
  f.close();
  uint32_t t2 = millis();

  uint32_t wms = (t1 - t0);
  uint32_t rms = (t2 - t1);

  char msg[52];
  snprintf(msg, sizeof(msg), "SD bench write=%lums read=%lums",
           (unsigned long)wms, (unsigned long)rms);
  logEvent(msg);

  display.clearDisplay();
  drawHeader("SD Bench");
  display.setCursor(0, 14); display.print("Write "); display.print(w); display.print("B ");
  display.print(wms); display.print("ms");
  display.setCursor(0, 26); display.print("Read  "); display.print(r); display.print("B ");
  display.print(rms); display.print("ms");
  display.setCursor(0, 56); display.print("Exit=Back");
  display.display();
}

// =============================
// Chip select init
// =============================
static void initChipSelectsSafe() {
  pinMode(SD_CS, OUTPUT);    digitalWrite(SD_CS, HIGH);

  pinMode(NRF1_CSN, OUTPUT); digitalWrite(NRF1_CSN, HIGH);
  pinMode(NRF2_CSN, OUTPUT); digitalWrite(NRF2_CSN, HIGH);

  pinMode(NRF1_CE, OUTPUT);  digitalWrite(NRF1_CE, LOW);
  pinMode(NRF2_CE, OUTPUT);  digitalWrite(NRF2_CE, LOW);
}
