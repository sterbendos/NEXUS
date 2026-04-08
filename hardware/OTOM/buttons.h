#pragma once

#include "globals.h"

// =============================
// Button update logic
// =============================
static void updateButton(Button &b, uint32_t now) {
  b.pressedEvent = false;
  bool raw = digitalRead(b.pin);

  if (raw != b.rawLast) {
    b.rawLast = raw;
    b.lastEdge = now;
  }

  if ((now - b.lastEdge) >= DEBOUNCE_MS && raw != b.stable) {
    bool prev = b.stable;
    b.stable = raw;
    if (prev == HIGH && b.stable == LOW) b.pressedEvent = true;
  }
}

static void updateButtons(uint32_t now) {
  updateButton(bUp, now);
  updateButton(bDown, now);
  updateButton(bEnter, now);
  updateButton(bExit, now);
  updateButton(bConfirm, now);

  if (bUp.pressedEvent || bDown.pressedEvent || bEnter.pressedEvent || bExit.pressedEvent || bConfirm.pressedEvent) {
    lastActivityMs = now;
  }
}
