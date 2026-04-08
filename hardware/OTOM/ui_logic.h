#pragma once

#include "globals.h"
#include "telemetry.h"
#include "ui_draw.h"
#include "sd_utils.h"
#include "rf_tools.h"
#include "jam.h"
#include "eyes.h"
#include "rfid_tools.h"
#include "doom.h"
#include "remote.h"

// =============================
// Signal delete/clear callbacks
// =============================
static void deleteSelectedSignal() {
  if (pendingSignalIndex >= 0) deleteSignalAt((uint8_t)pendingSignalIndex);
  int total = capturedCount + SIGNALS_ACTION_COUNT;
  if (capturedCount == 0) replayIndex = 1;
  else if (replayIndex >= total) replayIndex = total - 1;
  uiMode = UI_PAGE;
  page = PAGE_SIGNALS;
  drawSignalsPage();
}

static void clearAllSignalsConfirm() {
  clearAllSignals();
  replayIndex = 1;
  uiMode = UI_PAGE;
  page = PAGE_SIGNALS;
  drawSignalsPage();
}

// =============================
// Confirm helper (double-confirm)
// =============================
static void askConfirm2(const char* title, const char* actionText, void (*cb)()) {
  confirmReturnMode = uiMode;
  confirmReturnPage = page;
  confirmReturnSub = subMenu;
  confirmReturnMenuIndex = menuIndex;
  confirmReturnJamIndex = jamIndex;
  confirmReturnReplayIndex = replayIndex;
  confirmTitle = title;
  confirmAction = actionText;
  confirmCallback = cb;
  confirmArmed = false;
  confirmArmMs = 0;
  uiMode = UI_CONFIRM;
  drawConfirm();
}

// =============================
// Return from confirm
// =============================
static void returnFromConfirm() {
  uiMode = confirmReturnMode;
  page = confirmReturnPage;
  subMenu = confirmReturnSub;
  menuIndex = confirmReturnMenuIndex;
  jamIndex = confirmReturnJamIndex;
  replayIndex = confirmReturnReplayIndex;
  if (uiMode == UI_MENU) { drawMenu(); return; }
  if (uiMode == UI_SUBMENU) {
    if (subMenu == SUB_JAM) { drawJamMenu(); return; }
    uiMode = UI_MENU; subMenu = SUB_NONE; drawMenu(); return;
  }
  if (uiMode == UI_PAGE) {
    switch (page) {
      case PAGE_STATUS: drawStatusPage(); break;
      case PAGE_SPECTRUM: if (specDone) drawSpectrumResult(); else drawSpectrumPageIdle(); break;
      case PAGE_LINKTEST: drawLinkTestPageIdle(); break;
      case PAGE_CAPTURE: drawCapturePageIdle(); break;
      case PAGE_SIGNALS: drawSignalsPage(); break;
      case PAGE_MONITOR: drawMonitorPageIdle(); break;
      case PAGE_SD: drawSdPageIdle(); break;
      case PAGE_SETTINGS: drawSettings(); break;
      case PAGE_ABOUT: drawAbout(); break;
      case PAGE_FILES: drawFilesPage(); break;
      case PAGE_SESSION: drawSessionPage(); break;
      case PAGE_WIFI: drawWifiPage(); break;
      case PAGE_BLE: drawBlePage(); break;
      case PAGE_NFC: rfidMenuIndex=0; drawRfidMenu(); break;
      case PAGE_BADUSB: drawBadUsbPage(); break;
      case PAGE_DOOM: display.clearDisplay(); display.display(); break;
      default: uiMode = UI_MENU; page = PAGE_NONE; drawMenu(); break;
    }
    return;
  }
  if (uiMode == UI_IDLE_EYES) {
    idleEyesEnter();
    return;
  }
  uiMode = UI_MENU;
  page = PAGE_NONE;
  drawMenu();
}

// =============================
// Pages
// =============================
static void openPage(PageId p) {
  page = p;
  uiMode = UI_PAGE;
  refreshStatus();

  switch (page) {
    case PAGE_STATUS:    drawStatusPage(); logEvent("Page Status"); break;
    case PAGE_SPECTRUM:  drawSpectrumPageIdle(); logEvent("Page Spectrum"); break;
    case PAGE_LINKTEST:  drawLinkTestPageIdle(); logEvent("Page Link Test"); break;
    case PAGE_CAPTURE:   drawCapturePageIdle(); logEvent("Page Capture"); break;
    case PAGE_SIGNALS:   replayIndex = (capturedCount == 0) ? 1 : 0; drawSignalsPage(); logEvent("Page Signals"); break;
    case PAGE_MONITOR:   drawMonitorPageIdle(); logEvent("Page Monitor"); break;
    case PAGE_SD:        drawSdPageIdle(); logEvent("Page SD"); break;
    case PAGE_SETTINGS:  drawSettings(); logEvent("Page Settings"); break;
    case PAGE_ABOUT:     drawAbout(); logEvent("Page About"); break;
    case PAGE_FILES:     refreshFileList(); drawFilesPage(); logEvent("Page Files"); break;
    case PAGE_SESSION:   drawSessionPage(); logEvent("Page Session"); break;
    case PAGE_WIFI:      wifiScanned = false; drawWifiPage(); logEvent("Page Wi-Fi"); break;
    case PAGE_BLE:       drawBlePage(); logEvent("Page BLE"); break;
    case PAGE_NFC:       rfidMenuIndex=0; drawRfidMenu(); logEvent("Page NFC"); break;
    case PAGE_BADUSB:    drawBadUsbPage(); logEvent("Page BadUSB"); break;
    case PAGE_REMOTE:    replayIndex=0; drawRemotePage(); logEvent("Page Remote"); break;
    case PAGE_DOOM:      startDoom(); logEvent("Page DOOM"); break;
    default:             uiMode = UI_MENU; page = PAGE_NONE; drawMenu(); break;
  }
}

static void openSubMenu(SubMenuId sm) {
  subMenu = sm;
  uiMode = UI_SUBMENU;
  
  switch (subMenu) {
    case SUB_JAM: jamIndex = 0; drawJamMenu(); break;
    default: uiMode = UI_MENU; subMenu = SUB_NONE; drawMenu(); break;
  }
}

static void handleMenuEnter() {
  switch (menuIndex) {
    case 0: openPage(PAGE_STATUS);   break;
    case 1: openPage(PAGE_SPECTRUM); break;
    case 2: openPage(PAGE_LINKTEST); break;
    case 3: openPage(PAGE_CAPTURE);  break;
    case 4: openPage(PAGE_SIGNALS);  break;
    case 5: openPage(PAGE_MONITOR);  break;
    case 6: openSubMenu(SUB_JAM);    break;
    case 7: openPage(PAGE_SD);       break;
    case 8: openPage(PAGE_SETTINGS); break;
    case 9: openPage(PAGE_ABOUT);    break;
    case 10: openPage(PAGE_FILES);   break;
    case 11: openPage(PAGE_SESSION); break;
    case 12: openPage(PAGE_WIFI);    break;
    case 13: openPage(PAGE_BLE);     break;
    case 14: openPage(PAGE_NFC);     break;
    case 15: openPage(PAGE_BADUSB);  break;
    case 16: openPage(PAGE_REMOTE);  break;
    case 17: openPage(PAGE_DOOM);    break;
  }
}
