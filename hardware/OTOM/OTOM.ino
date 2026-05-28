// =============================
// OTOM / NEXUS Firmware
// =============================
// Modular split — each header contains one logical subsystem.
// All files must live in the same sketch folder for Arduino IDE.

#include "config.h"
#include "types.h"
#include "globals.h"
#include "buttons.h"
#include "eyes.h"
#include "telemetry.h"
#include "ui_draw.h"
#include "sd_utils.h"
#include "rf_tools.h"
#include "jam.h"
#include "rfid_tools.h"
#include "ui_logic.h"
#include "badusb.h"
#include "wifi_tools.h"
#include "ble_spam.h"

// =============================
// Setup
// =============================
void setup() {
  randomSeed((uint32_t)micros());
  initTelemetryOutput();

  pinMode(BTN_UP, INPUT_PULLUP);
  pinMode(BTN_DOWN, INPUT_PULLUP);
  pinMode(BTN_ENTER, INPUT_PULLUP);
  pinMode(BTN_EXIT, INPUT_PULLUP);
  pinMode(BTN_CONFIRM, INPUT_PULLUP);

  initChipSelectsSafe();

  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(400000);

  if (!display.begin(OLED_ADDR, true)) for(;;) { delay(100); }
  display.clearDisplay();
  display.display();

  SPI.begin(NRF_SPI_SCK, NRF_SPI_MISO, NRF_SPI_MOSI);
  sdSPI.begin(SD_SPI_SCK, SD_SPI_MISO, SD_SPI_MOSI, SD_CS);

  eyes.begin(128, 64, 120);
  eyes.setDisplayColors(0, 1);

  sdReady  = mountSd();
  nrf1Ready = radio1.begin();          // Radio 1 on FSPI (default SPI)
  nrf2Ready = radio2.begin(&sdSPI);    // Radio 2 on HSPI (shared with SD, separate CSN)
  refreshStatus();

  memset(capturedSignals, 0, sizeof(capturedSignals));
  capturedCount = 0;

  uiMode = UI_MENU;
  page = PAGE_NONE;
  subMenu = SUB_NONE;
  runMode = RUN_NONE;
  lastActivityMs = millis();
  telemetryLastHeartbeat = lastActivityMs;
  drawMenu();
  emitTelemetry("boot", "info", "Firmware ready", false);
}

// =============================
// Loop
// =============================
void loop() {
  uint32_t now = millis();
  updateButtons(now);
  telemetryTick(now);

  // Handle running tools
  if (runMode == RUN_SPECTRUM) {
    if (bExit.pressedEvent) { runMode = RUN_NONE; logEvent("Spectrum stop"); drawSpectrumPageIdle(); }
    else spectrumStep();
    return;
  }
  if (runMode == RUN_LINKTEST) {
    if (bExit.pressedEvent) { runMode = RUN_NONE; logEvent("Link test stop"); drawLinkTestPageIdle(); }
    else linkTestStep(now);
    return;
  }
  if (runMode == RUN_CAPTURE) {
    if (bExit.pressedEvent) { runMode = RUN_NONE; logEvent("Capture stop"); drawCapturePageIdle(); }
    else captureStep();
    return;
  }
  if (runMode == RUN_MONITOR) {
    if (bExit.pressedEvent) { runMode = RUN_NONE; logEvent("Monitor stop"); drawMonitorPageIdle(); }
    else monitorStep();
    return;
  }
  
  // Handle RFID Scanning
  if (isRfidScanning) {
    if (bExit.pressedEvent) { isRfidScanning = false; drawRfidMenu(); logEvent("RFID read stop"); }
    else rfidReadStep();
    return;
  }
  
  // Jamming modes - stop carrier and return to menu
  if (runMode == RUN_JAM_BT) {
    if (bExit.pressedEvent) { 
      radio1.stopConstCarrier(); 
      radio2.stopConstCarrier(); 
      runMode = RUN_NONE; 
      logEvent("Jam BT stop");
      openSubMenu(SUB_JAM); 
    }
    else jamBTStep();
    return;
  }
  if (runMode == RUN_JAM_BLE) {
    if (bExit.pressedEvent) { 
      radio1.stopConstCarrier(); 
      radio2.stopConstCarrier(); 
      runMode = RUN_NONE; 
      logEvent("Jam BLE stop");
      openSubMenu(SUB_JAM); 
    }
    else jamBLEStep();
    return;
  }
  if (runMode == RUN_JAM_ALL) {
    if (bExit.pressedEvent) { 
      radio1.stopConstCarrier(); 
      radio2.stopConstCarrier(); 
      runMode = RUN_NONE; 
      logEvent("Jam ALL stop");
      openSubMenu(SUB_JAM); 
    }
    else jamALLStep();
    return;
  }
  if (runMode == RUN_JAM_CUSTOM) {
    if (bExit.pressedEvent) { 
      radio1.stopConstCarrier(); 
      radio2.stopConstCarrier(); 
      runMode = RUN_NONE; 
      logEvent("Jam custom stop");
      openSubMenu(SUB_JAM); 
    }
    else jamCustomStep();
    return;
  }

  // DOOM (Easter Egg)
  if (runMode == RUN_DOOM) {
    doomStep();
    return;
  }

  // WiFi Attack
  if (runMode == RUN_WIFI_ATTACK) {
    if (bExit.pressedEvent || bEnter.pressedEvent) {
      startWifiAttack(); // toggle off
      runMode = RUN_NONE;
      uiMode = UI_PAGE;
      page = PAGE_WIFI;
      drawWifiPage();
    }
    else wifiAttackStep();
    return;
  }

  // BLE Spam
  if (runMode == RUN_BLE_SPAM) {
    if (bExit.pressedEvent || bEnter.pressedEvent) {
      startBleSpam(); // toggle off
      runMode = RUN_NONE;
      uiMode = UI_PAGE;
      page = PAGE_BLE;
      drawBlePage();
    }
    else bleSpamStep();
    return;
  }

  // Inactivity -> idle eyes
  if (uiMode != UI_IDLE_EYES && uiMode != UI_CONFIRM && runMode == RUN_NONE &&
      (now - lastActivityMs) >= IDLE_TIMEOUT_MS) {
    uiMode = UI_IDLE_EYES;
    idleEyesEnter();
  }

  // Idle eyes mode
  if (uiMode == UI_IDLE_EYES) {
    if (bUp.pressedEvent || bDown.pressedEvent || bEnter.pressedEvent || bExit.pressedEvent || bConfirm.pressedEvent) {
      uiMode = UI_MENU;
      page = PAGE_NONE;
      drawMenu();
      return;
    }
    eyes.update();
    moodTick();
    fxTick();
    return;
  }

  // Confirm mode
  if (uiMode == UI_CONFIRM) {
    if (confirmArmed && (now - confirmArmMs) > 5000) {
      confirmArmed = false;
      drawConfirm();
    }

    if (bExit.pressedEvent) {
      returnFromConfirm();
      return;
    }
    if (bConfirm.pressedEvent) {
      if (!confirmArmed) {
        confirmArmed = true;
        confirmArmMs = now;
        drawConfirm();
      } else {
        confirmArmed = false;
        if (confirmCallback) confirmCallback();
      }
      return;
    }
    return;
  }

  // Submenu mode
  if (uiMode == UI_SUBMENU) {
    if (bExit.pressedEvent) {
      uiMode = UI_MENU;
      subMenu = SUB_NONE;
      drawMenu();
      return;
    }

    if (subMenu == SUB_JAM) {
      if (bUp.pressedEvent) {
        jamIndex = (jamIndex - 1 + JAM_COUNT) % JAM_COUNT;
        drawJamMenu();
      } else if (bDown.pressedEvent) {
        jamIndex = (jamIndex + 1) % JAM_COUNT;
        drawJamMenu();
      } else if (bEnter.pressedEvent) {
        switch (jamIndex) {
          case 0: askConfirm2("Jam BT", "Start BT jam?", startJamBT); break;
          case 1: askConfirm2("Jam BLE", "Start BLE jam?", startJamBLE); break;
          case 2: askConfirm2("Jam ALL", "Start full jam?", startJamALL); break;
          case 3: askConfirm2("Custom", "Start custom?", startJamCustom); break;
        }
      }
    }
    return;
  }

  // Page mode
  if (uiMode == UI_PAGE) {
    if (bExit.pressedEvent) {
      uiMode = UI_MENU;
      page = PAGE_NONE;
      drawMenu();
      return;
    }

    if (page == PAGE_STATUS && bEnter.pressedEvent) {
      refreshStatus();
      drawStatusPage();
      return;
    }

    if (page == PAGE_SPECTRUM) {
      if (specDone && bEnter.pressedEvent) { specDone = false; drawSpectrumPageIdle(); return; }
      if (!specDone && bEnter.pressedEvent) {
        askConfirm2("Spectrum", "Start scan?", startSpectrumScan);
        return;
      }
    }

    if (page == PAGE_LINKTEST && bEnter.pressedEvent) {
      askConfirm2("Link Test", "Start test?", startLinkTest);
      return;
    }

    if (page == PAGE_CAPTURE && bEnter.pressedEvent) {
      askConfirm2("Capture", "Start capture?", startCapture);
      return;
    }

    if (page == PAGE_SIGNALS) {
      int total = capturedCount + SIGNALS_ACTION_COUNT;
      if (bUp.pressedEvent) {
        replayIndex = (replayIndex - 1 + total) % total;
        drawSignalsPage();
      } else if (bDown.pressedEvent) {
        replayIndex = (replayIndex + 1) % total;
        drawSignalsPage();
      } else if (bEnter.pressedEvent) {
        if (replayIndex < (int)capturedCount && capturedCount > 0) {
          askConfirm2("Replay", "Replay signal?", replaySelectedSignal);
        } else {
          int action = replayIndex - capturedCount;
          if (action == 0) {
            bool ok = saveSignalsToSd();
            showQuickMessage("Signals", ok ? "Saved to SD" : "Save failed", nullptr);
            drawSignalsPage();
          } else if (action == 1) {
            bool ok = loadSignalsFromSd();
            replayIndex = (capturedCount == 0) ? 1 : 0;
            showQuickMessage("Signals", ok ? "Loaded from SD" : "Load failed", nullptr);
            drawSignalsPage();
          } else if (action == 2) {
            askConfirm2("Clear All", "Delete all?", clearAllSignalsConfirm);
          }
        }
      } else if (bConfirm.pressedEvent) {
        if (replayIndex < (int)capturedCount && capturedCount > 0) {
          pendingSignalIndex = replayIndex;
          askConfirm2("Delete", "Delete signal?", deleteSelectedSignal);
        }
      }
      return;
    }

    if (page == PAGE_MONITOR && bEnter.pressedEvent) {
      askConfirm2("Monitor", "Start monitor?", startMonitor);
      return;
    }

    if (page == PAGE_SD) {
      if (bEnter.pressedEvent) {
        sdReady = mountSd();
        refreshStatus();
        drawSdPageIdle();
        return;
      }
      if (bConfirm.pressedEvent) {
        askConfirm2("SD Bench", "Run bench?", runSdBenchOnce);
        return;
      }
    }

    if (page == PAGE_FILES) {
      if (bUp.pressedEvent && fileCount > 0) {
        fileIndex = (fileIndex - 1 + fileCount) % fileCount;
        drawFilesPage();
      } else if (bDown.pressedEvent && fileCount > 0) {
        fileIndex = (fileIndex + 1) % fileCount;
        drawFilesPage();
      } else if (bEnter.pressedEvent) {
        if (!sdReady) { sdReady = mountSd(); refreshStatus(); }
        refreshFileList();
        drawFilesPage();
      }
      return;
    }

    if (page == PAGE_SESSION) {
      if (bEnter.pressedEvent) {
        if (sessionOn) askConfirm2("Session", "Stop session?", stopSession);
        else askConfirm2("Session", "Start session?", startSession);
      }
      return;
    }

    if (page == PAGE_WIFI) {
      if (bEnter.pressedEvent) {
        wifiScan();
      } else if (bConfirm.pressedEvent) {
        askConfirm2("Beacon Spam", "Start Attack?", [](){
          startWifiAttack();
          runMode = RUN_WIFI_ATTACK;
        });
      }
      return;
    }

    if (page == PAGE_BLE) {
      if (bEnter.pressedEvent) {
        askConfirm2("BLE Spam", "Spam iPhones?", [](){
          startBleSpam();
          runMode = RUN_BLE_SPAM;
        });
      }
      return;
    }

    if (page == PAGE_BADUSB) {
      if (bEnter.pressedEvent) {
        startBadUSB();
      }
      return;
    }

    if (page == PAGE_NFC) {
      if (bUp.pressedEvent) {
        rfidMenuIndex = (rfidMenuIndex - 1 + 2) % 2;
        drawRfidMenu();
      } else if (bDown.pressedEvent) {
        rfidMenuIndex = (rfidMenuIndex + 1) % 2;
        drawRfidMenu();
      } else if (bEnter.pressedEvent) {
        if (rfidMenuIndex == 0) startRfidRead();
        else startRfidSimulate();
      }
      return;
    }

    if (page == PAGE_REMOTE) {
      const int count = 4;
      if (bUp.pressedEvent) { replayIndex = (replayIndex - 1 + count) % count; drawRemotePage(); }
      else if (bDown.pressedEvent) { replayIndex = (replayIndex + 1) % count; drawRemotePage(); }
      else if (bEnter.pressedEvent) {
        switch (replayIndex) {
          case 0: sendRemoteExec("terminal", ""); break;
          case 1: sendRemoteExec("calc", "");     break;
          case 2: sendRemoteExec("github", "");   break;
          case 3: emitTelemetry("REMOTE", "info", "Ping from OTOM", false); break;
        }
      }
      return;
    }

    return;
  }

  // Menu mode
  if (uiMode == UI_MENU) {
    if (bUp.pressedEvent) {
      menuIndex = (menuIndex - 1 + MAIN_COUNT) % MAIN_COUNT;
      drawMenu();
    } else if (bDown.pressedEvent) {
      menuIndex = (menuIndex + 1) % MAIN_COUNT;
      drawMenu();
    } else if (bEnter.pressedEvent) {
      handleMenuEnter();
    } else if (bExit.pressedEvent) {
      openPage(PAGE_STATUS);
    }
  }
}
