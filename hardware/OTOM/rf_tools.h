#pragma once

#include "globals.h"
#include "telemetry.h"
#include "ui_draw.h"

// =============================
// Radio configuration helpers
// =============================
static void configureRadioForScan(RF24 &r) {
  r.setAutoAck(false);
  r.setRetries(0, 0);
  r.setDataRate(RF24_2MBPS);
  r.setPALevel(RF24_PA_LOW);
  r.setCRCLength(RF24_CRC_DISABLED);
}

static void configureRadioForLink(RF24 &r) {
  r.setAutoAck(true);
  r.setRetries(3, 5);
  r.setDataRate(RF24_1MBPS);
  r.setPALevel(RF24_PA_LOW);
  r.setCRCLength(RF24_CRC_16);
}

static void configureRadioForCapture(RF24 &r) {
  r.setAutoAck(false);
  r.setRetries(0, 0);
  r.setDataRate(RF24_2MBPS);
  r.setPALevel(RF24_PA_MAX);
  r.setCRCLength(RF24_CRC_DISABLED);
  r.enableDynamicPayloads();
}

static void configureRadioForJam(RF24 &r, int channel) {
  r.stopListening();
  r.setAutoAck(false);
  r.setRetries(0, 0);
  r.setPALevel(RF24_PA_MAX);
  r.setDataRate(RF24_2MBPS);
  r.setCRCLength(RF24_CRC_DISABLED);
  r.setChannel(channel);
  r.startConstCarrier(RF24_PA_MAX, channel);
}

// =============================
// TOOL 1: Spectrum Activity Scan
// =============================
static void startSpectrumScan() {
  memset(specVals, 0, sizeof(specVals));
  specRep = 0;
  specChA = 0;
  specChB = 63;
  specDone = false;

  configureRadioForScan(radio1);
  configureRadioForScan(radio2);

  runMode = RUN_SPECTRUM;
  logEvent("Spectrum start");
  drawSpectrumRunning();
}

static void spectrumStep() {
  if (specRep >= SPEC_REPS) {
    runMode = RUN_NONE;
    specDone = true;
    logEvent("Spectrum done");
    drawSpectrumResult();
    return;
  }

  radio1.setChannel(specChA);
  radio1.startListening();

  if (specChB < NUM_CH) {
    radio2.setChannel(specChB);
    radio2.startListening();
  }

  delayMicroseconds(140);

  if (radio1.testRPD()) specVals[specChA]++;
  radio1.stopListening();

  if (specChB < NUM_CH) {
    if (radio2.testRPD()) specVals[specChB]++;
    radio2.stopListening();
  }

  specChA++;
  specChB++;

  if (specChA > 62) { specChA = 0; specChB = 63; specRep++; }

  if ((specChA % 8) == 0) drawSpectrumRunning();
}

// =============================
// TOOL 2: Dual-Radio Link Test
// =============================
static void startLinkTest() {
  configureRadioForLink(radio1);
  configureRadioForLink(radio2);

  radio1.stopListening();
  radio2.stopListening();

  radio1.setChannel(76);
  radio2.setChannel(76);

  radio1.openReadingPipe(1, ADDR_B);
  radio2.openReadingPipe(1, ADDR_A);

  ltTx = 0; ltRx = 0;
  ltState = 0;
  ltLastMs = millis();

  runMode = RUN_LINKTEST;
  logEvent("Link test start");
  drawLinkRunning();
}

static void linkTestStep(uint32_t now) {
  if (now - ltLastMs < 25) return;
  ltLastMs = now;

  uint32_t msg = now;

  switch (ltState) {
    case 0: {
      radio2.startListening();
      radio1.stopListening();

      radio1.openWritingPipe(ADDR_A);
      bool ok = radio1.write(&msg, sizeof(msg));
      (void)ok;
      ltTx++;

      ltDeadline = now + 10;
      ltState = 1;
      break;
    }
    case 1: {
      if (radio2.available()) {
        uint32_t in;
        radio2.read(&in, sizeof(in));
        ltRx++;
      }
      if ((int32_t)(now - ltDeadline) >= 0) {
        radio2.stopListening();
        ltState = 2;
      }
      break;
    }
    case 2: {
      radio1.startListening();
      radio2.stopListening();

      radio2.openWritingPipe(ADDR_B);
      bool ok = radio2.write(&msg, sizeof(msg));
      (void)ok;
      ltTx++;

      ltDeadline = now + 10;
      ltState = 3;
      break;
    }
    case 3: {
      if (radio1.available()) {
        uint32_t in;
        radio1.read(&in, sizeof(in));
        ltRx++;
      }
      if ((int32_t)(now - ltDeadline) >= 0) {
        radio1.stopListening();
        ltState = 0;
      }
      break;
    }
  }

  if ((ltTx % 8) == 0) drawLinkRunning();
}

// =============================
// TOOL 3: Signal Capture
// =============================
static void startCapture() {
  if (capturedCount >= 10) {
    display.clearDisplay();
    drawHeader("Capture Full");
    display.setTextColor(1);
    display.setCursor(0, 24); display.print("10/10 slots used");
    display.setCursor(0, 34); display.print("Delete signals first");
    display.setCursor(0, 56); display.print("Exit=Back");
    display.display();
    return;
  }

  configureRadioForCapture(radio1);
  capPackets = 0;
  capCh = 0;
  capAddr = 0;
  runMode = RUN_CAPTURE;
  logEvent("Capture start");
  drawCaptureRunning();
}

static void captureStep() {
  if (capturedCount >= 10) {
    runMode = RUN_NONE;
    logEvent("Capture done");
    drawCaptureResult(false);
    return;
  }

  if (capCh >= NUM_CH) {
    runMode = RUN_NONE;
    logEvent("Capture done");
    drawCaptureResult(capturedCount > 0);
    return;
  }

  radio1.setChannel(capCh);
  radio1.openReadingPipe(1, commonAddresses[capAddr]);
  radio1.startListening();

  uint32_t timeout = millis() + 50;
  while (millis() < timeout) {
    if (radio1.available()) {
      uint8_t payload[32];
      uint8_t size = radio1.getDynamicPayloadSize();

      if (size > 0 && size <= 32) {
        radio1.read(payload, size);
        capPackets++;

        capturedSignals[capturedCount].channel = capCh;
        memcpy(capturedSignals[capturedCount].address, commonAddresses[capAddr], 5);
        memcpy(capturedSignals[capturedCount].payload, payload, size);
        capturedSignals[capturedCount].payloadSize = size;
        capturedSignals[capturedCount].isValid = true;

        capturedCount++;
        char msg[56];
        snprintf(msg, sizeof(msg),
                 "Capture hit ch=%u size=%u slot=%u",
                 (unsigned)capCh, (unsigned)size, (unsigned)(capturedCount - 1));
        logEvent(msg);
        radio1.stopListening();
        runMode = RUN_NONE;
        logEvent("Capture done");
        drawCaptureResult(true);
        return;
      }
    }
  }

  radio1.stopListening();
  capAddr++;
  if (capAddr >= 8) {
    capAddr = 0;
    capCh++;
    if (capCh % 10 == 0) drawCaptureRunning();
  }
}

// =============================
// TOOL 4: Replay Signal
// =============================
static void replaySelectedSignal() {
  if (replayIndex >= capturedCount) return;
  char msg[24];
  snprintf(msg, sizeof(msg), "Replay #%d", replayIndex);
  logEvent(msg);

  display.clearDisplay();
  drawHeader("Replaying...");
  display.setTextColor(1);
  display.setCursor(0, 18); display.print("Signal #"); display.print(replayIndex);
  display.setCursor(0, 28); display.print("Transmitting...");
  display.display();

  CapturedSignal* sig = &capturedSignals[replayIndex];

  radio1.stopListening();
  radio2.stopListening();
  radio1.setChannel(sig->channel);
  radio2.setChannel(sig->channel);
  radio1.openWritingPipe(sig->address);
  radio2.openWritingPipe(sig->address);

  uint8_t success = 0;
  for (uint8_t i = 0; i < 20; i++) {
    bool r1 = radio1.write(sig->payload, sig->payloadSize);
    bool r2 = radio2.write(sig->payload, sig->payloadSize);
    if (r1 || r2) success++;
    delay(50);
  }

  display.clearDisplay();
  drawHeader("Replay Complete");
  display.setTextColor(1);
  display.setCursor(0, 18); display.print("Signal: #"); display.print(replayIndex);
  display.setCursor(0, 28); display.print("Success: "); display.print(success); display.print("/20");
  display.setCursor(0, 38); display.print("Rate: "); display.print((success * 100) / 20); display.print("%");
  display.setCursor(0, 56); display.print("Exit=Back");
  display.display();

  char msg2[44];
  snprintf(msg2, sizeof(msg2), "Replay #%d success=%u/20", replayIndex, (unsigned)success);
  logEvent(msg2);
}

// =============================
// TOOL 5: Monitor Mode
// =============================
static void startMonitor() {
  configureRadioForCapture(radio1);
  monPackets = 0;
  monCh = 0;
  monAddr = 0;
  runMode = RUN_MONITOR;
  logEvent("Monitor start");
  drawMonitorRunning();
}

static void monitorStep() {
  radio1.setChannel(monCh);
  radio1.openReadingPipe(1, commonAddresses[monAddr]);
  radio1.startListening();
  delayMicroseconds(800);

  if (radio1.available()) {
    uint8_t payload[32];
    uint8_t size = radio1.getDynamicPayloadSize();

    if (size > 0 && size <= 32) {
      radio1.read(payload, size);
      monPackets++;
      if (monPackets % 5 == 0) drawMonitorRunning();
    }
  }

  radio1.stopListening();
  monAddr++;
  if (monAddr >= 8) {
    monAddr = 0;
    monCh += 2;
    if (monCh >= NUM_CH) monCh = 0;
  }
}
