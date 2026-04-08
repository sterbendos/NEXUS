#pragma once

#include "globals.h"

// =============================
// Telemetry helpers
// =============================
static const char* uiModeName(UiMode mode) {
  switch (mode) {
    case UI_MENU: return "menu";
    case UI_PAGE: return "page";
    case UI_IDLE_EYES: return "idle_eyes";
    case UI_CONFIRM: return "confirm";
    case UI_SUBMENU: return "submenu";
    default: return "unknown";
  }
}

static const char* pageName(PageId p) {
  switch (p) {
    case PAGE_NONE: return "none";
    case PAGE_STATUS: return "status";
    case PAGE_SPECTRUM: return "spectrum";
    case PAGE_LINKTEST: return "linktest";
    case PAGE_SD: return "sd";
    case PAGE_SETTINGS: return "settings";
    case PAGE_ABOUT: return "about";
    case PAGE_CAPTURE: return "capture";
    case PAGE_SIGNALS: return "signals";
    case PAGE_REPLAY: return "replay";
    case PAGE_MONITOR: return "monitor";
    case PAGE_JAM: return "jam";
    case PAGE_FILES: return "files";
    case PAGE_SESSION: return "session";
    case PAGE_WIFI: return "wifi";
    case PAGE_BLE: return "ble";
    case PAGE_NFC: return "nfc";
    case PAGE_BADUSB: return "badusb";
    default: return "unknown";
  }
}

static const char* runModeName(RunMode mode) {
  switch (mode) {
    case RUN_NONE: return "none";
    case RUN_SPECTRUM: return "spectrum";
    case RUN_LINKTEST: return "linktest";
    case RUN_SDBENCH: return "sdbench";
    case RUN_CAPTURE: return "capture";
    case RUN_MONITOR: return "monitor";
    case RUN_JAM_BT: return "jam_bt";
    case RUN_JAM_BLE: return "jam_ble";
    case RUN_JAM_ALL: return "jam_all";
    case RUN_JAM_CUSTOM: return "jam_custom";
    default: return "unknown";
  }
}

static void jsonEscapedPrint(Print& out, const char* text) {
  if (!text) return;
  while (*text) {
    char c = *text++;
    if (c == '"' || c == '\\') {
      out.write('\\');
      out.write(c);
    } else if (c == '\n') {
      out.print("\\n");
    } else if (c == '\r') {
      out.print("\\r");
    } else if ((uint8_t)c < 32) {
      out.write(' ');
    } else {
      out.write(c);
    }
  }
}

static void telemetryGetIp(char* out, size_t outLen) {
  IPAddress ip = WiFi.localIP();
  snprintf(out, outLen, "%u.%u.%u.%u", ip[0], ip[1], ip[2], ip[3]);
}

static void telemetryGetMac(char* out, size_t outLen) {
  uint8_t mac[6] = {0, 0, 0, 0, 0, 0};
  WiFi.macAddress(mac);
  snprintf(out, outLen, "%02X:%02X:%02X:%02X:%02X:%02X",
           mac[0], mac[1], mac[2], mac[3], mac[4], mac[5]);
}

static void telemetryTryStartTcpServer() {
  if (WiFi.status() != WL_CONNECTED) {
    if (telemetryTcpStarted) {
      for (uint8_t i = 0; i < 3; i++) {
        if (telemetryClients[i]) telemetryClients[i].stop();
      }
    }
    telemetryTcpStarted = false;
    return;
  }

  if (telemetryTcpStarted) return;
  telemetryServer.begin();
  telemetryServer.setNoDelay(true);
  telemetryTcpStarted = true;
}

static void telemetryAcceptClients() {
  telemetryTryStartTcpServer();
  if (!telemetryTcpStarted) return;

  WiFiClient incoming = telemetryServer.available();
  if (!incoming) return;

  for (uint8_t i = 0; i < 3; i++) {
    if (!telemetryClients[i] || !telemetryClients[i].connected()) {
      if (telemetryClients[i]) telemetryClients[i].stop();
      telemetryClients[i] = incoming;
      return;
    }
  }
  incoming.stop();
}

static void telemetryWriteLine(
  Print& out,
  uint32_t seq,
  const char* channel,
  const char* eventType,
  const char* severity,
  const char* message,
  bool anomaly
) {
  char ipText[16];
  char macText[18];
  telemetryGetIp(ipText, sizeof(ipText));
  telemetryGetMac(macText, sizeof(macText));

  out.print("{\"timestamp\":\"");
  out.print((unsigned long)millis());
  out.print("\",\"device_id\":\"");
  jsonEscapedPrint(out, telemetryDeviceId);
  out.print("\",\"source\":\"esp32-firmware\"");
  out.print(",\"channel\":\"");
  jsonEscapedPrint(out, channel);
  out.print("\",\"event_id\":\"");
  out.print((unsigned long)seq);
  out.print("\",\"event_type\":\"");
  jsonEscapedPrint(out, eventType);
  out.print("\",\"severity\":\"");
  jsonEscapedPrint(out, severity);
  out.print("\",\"message\":\"");
  jsonEscapedPrint(out, message);
  out.print("\",\"anomaly\":");
  out.print(anomaly ? "true" : "false");

  out.print(",\"network\":{\"ip\":\"");
  jsonEscapedPrint(out, ipText);
  out.print("\",\"mac\":\"");
  jsonEscapedPrint(out, macText);
  out.print("\"}");

  out.print(",\"metrics\":{");
  out.print("\"sd_ready\":"); out.print(sdReady ? 1 : 0);
  out.print(",\"nrf1_ready\":"); out.print(nrf1Ready ? 1 : 0);
  out.print(",\"nrf2_ready\":"); out.print(nrf2Ready ? 1 : 0);
  out.print(",\"session_on\":"); out.print(sessionOn ? 1 : 0);
  out.print(",\"captured_count\":"); out.print((unsigned)capturedCount);
  out.print(",\"wifi_count\":"); out.print((unsigned)wifiCount);
  out.print(",\"file_count\":"); out.print((unsigned)fileCount);
  out.print(",\"menu_index\":"); out.print(menuIndex);
  out.print("}");

  out.print(",\"events\":[{\"name\":\"");
  jsonEscapedPrint(out, eventType);
  out.print("\",\"message\":\"");
  jsonEscapedPrint(out, message);
  out.print("\"}]");

  out.print(",\"state\":{\"ui_mode\":\"");
  jsonEscapedPrint(out, uiModeName(uiMode));
  out.print("\",\"page\":\"");
  jsonEscapedPrint(out, pageName(page));
  out.print("\",\"run_mode\":\"");
  jsonEscapedPrint(out, runModeName(runMode));
  out.print("\"}}");
  out.println();
}

static void emitTelemetry(const char* eventType, const char* severity, const char* message, bool anomaly = false) {
  telemetryAcceptClients();

  uint32_t seq = telemetrySeq++;
  telemetryWriteLine(
    Serial,
    seq,
    "serial",
    eventType ? eventType : "event",
    severity ? severity : "info",
    message ? message : "",
    anomaly
  );

  for (uint8_t i = 0; i < 3; i++) {
    if (!telemetryClients[i] || !telemetryClients[i].connected()) {
      if (telemetryClients[i]) telemetryClients[i].stop();
      continue;
    }
    telemetryWriteLine(
      telemetryClients[i],
      seq,
      "tcp",
      eventType ? eventType : "event",
      severity ? severity : "info",
      message ? message : "",
      anomaly
    );
  }
}

static void initTelemetryOutput() {
  Serial.begin(115200);
  delay(20);

  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);

  uint8_t mac[6] = {0, 0, 0, 0, 0, 0};
  WiFi.macAddress(mac);
  snprintf(telemetryDeviceId, sizeof(telemetryDeviceId),
           "OTOM-%02X%02X%02X", mac[3], mac[4], mac[5]);

  if (NEXUS_WIFI_SSID[0] != '\0') {
    WiFi.begin(NEXUS_WIFI_SSID, NEXUS_WIFI_PASS);
    uint32_t t0 = millis();
    while (WiFi.status() != WL_CONNECTED && (millis() - t0) < 4000) {
      delay(50);
    }
  }
  telemetryTryStartTcpServer();
}

static void telemetryTick(uint32_t now) {
  telemetryAcceptClients();
  if ((uint32_t)(now - telemetryLastHeartbeat) < TELEMETRY_HEARTBEAT_MS) return;
  telemetryLastHeartbeat = now;
  emitTelemetry("heartbeat", "info", "Periodic status", false);
}

static void logEvent(const char* msg) {
  emitTelemetry("event", "info", msg ? msg : "", false);
  if (!sessionOn || !sdReady || sessionPath[0] == 0) return;
  File f = SD.open(sessionPath, FILE_WRITE);
  if (!f) return;
  f.print(millis());
  f.print(" ");
  f.println(msg);
  f.close();
}
