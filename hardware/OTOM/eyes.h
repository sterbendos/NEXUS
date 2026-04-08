#pragma once

#include "globals.h"

// =============================
// Idle eyes animation
// =============================
static const uint8_t EYE_W = 28;
static const uint8_t EYE_H = 34;
static const uint8_t EYE_R = 10;
static const int     EYE_GAP = 56;

enum {P_IDLE, P_SQUASH, P_STRETCH, P_BACK} pstate = P_IDLE;
static uint32_t pAt = 0, nextPop = 0, nextMood = 0, flickerOff = 0;

static void baseShape(){
  eyes.setWidth(EYE_W, EYE_W);
  eyes.setHeight(EYE_H, EYE_H);
  eyes.setBorderradius(EYE_R, EYE_R);
  eyes.setSpacebetween(EYE_GAP);
}

static void popStart(){
  pstate = P_SQUASH; pAt = millis();
  eyes.setWidth(EYE_W - 4, EYE_W - 4);
  eyes.setHeight(EYE_H - 3, EYE_H - 3);
  eyes.setBorderradius(EYE_R + 2, EYE_R + 2);
}

static void popTick(){
  uint32_t now = millis();
  if(pstate == P_SQUASH && (int32_t)(now - (pAt + 70)) >= 0){
    pstate = P_STRETCH; pAt = now;
    eyes.setWidth(EYE_W + 4, EYE_W + 4);
    eyes.setHeight(EYE_H + 3, EYE_H + 3);
    eyes.setBorderradius(EYE_R - 1, EYE_R - 1);
  } else if(pstate == P_STRETCH && (int32_t)(now - (pAt + 90)) >= 0){
    pstate = P_BACK; pAt = now;
    baseShape();
  } else if(pstate == P_BACK && (int32_t)(now - (pAt + 140)) >= 0){
    pstate = P_IDLE;
    nextPop = now + (uint32_t)random(700, 1700);
  }
}

static void moodTick(){
  uint32_t now = millis();
  if((int32_t)(now - nextMood) < 0) return;
  uint8_t r = random(100);
  if      (r < 55) eyes.setMood(DEFAULT);
  else if (r < 72) eyes.setMood(HAPPY);
  else if (r < 88) eyes.setMood(TIRED);
  else             eyes.setMood(ANGRY);
  nextMood = now + (uint32_t)random(1800, 4200);
}

static void fxTick(){
  uint32_t now = millis();

  if(flickerOff && (int32_t)(now - flickerOff) >= 0){
    eyes.setHFlicker(OFF, 0);
    flickerOff = 0;
  }

  if(pstate == P_IDLE && (int32_t)(now - nextPop) >= 0){
    if(random(100) < 35) eyes.blink();
    if(random(100) < 14) eyes.anim_confused();
    if(random(100) < 10) eyes.anim_laugh();
    if(random(100) < 18){
      eyes.setHFlicker(ON, 1);
      flickerOff = now + (uint32_t)random(180, 420);
    }
    popStart();
  }

  if(pstate != P_IDLE) popTick();
}

static void idleEyesEnter(){
  baseShape();
  eyes.setCuriosity(ON);
  eyes.setAutoblinker(ON, 2, 2);
  eyes.setIdleMode(ON, 1, 2);
  eyes.open();

  uint32_t now = millis();
  nextPop = now + 500;
  nextMood = now + 1200;
  pstate = P_IDLE;
  flickerOff = 0;
}
