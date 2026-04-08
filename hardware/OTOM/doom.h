#pragma once

#include "globals.h"
#include <math.h>

#define MAP_WIDTH 8
#define MAP_HEIGHT 8

static const uint8_t DOOM_MAP[MAP_HEIGHT][MAP_WIDTH] = {
  {1,1,1,1,1,1,1,1},
  {1,0,0,0,0,0,0,1},
  {1,0,1,0,0,1,0,1},
  {1,0,1,0,0,1,0,1},
  {1,0,0,0,0,0,0,1},
  {1,0,1,1,0,0,0,1},
  {1,0,0,0,0,0,0,1},
  {1,1,1,1,1,1,1,1}
};

static float dPosX = 2.0f;
static float dPosY = 2.0f;
static float dDirX = -1.0f;
static float dDirY = 0.0f;
static float dPlaneX = 0.0f;
static float dPlaneY = 0.66f;

static void startDoom() {
  dPosX = 2.5f;
  dPosY = 2.5f;
  dDirX = -1.0f;
  dDirY = 0.0f;
  dPlaneX = 0.0f;
  dPlaneY = 0.66f;

  runMode = RUN_DOOM;
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(1);
  display.setCursor(20, 20);
  display.print("E1M1: Loading...");
  display.display();
  delay(1000);
}

static void doomStep() {
  display.clearDisplay();
  
  // Floor & Ceiling 
  // For standard 1-bit OLED we don't draw textured floors/ceilings, just black space
  
  // Raycast
  for(int x = 0; x < 128; x++) {
    float cameraX = 2 * x / 128.0f - 1; 
    float rayDirX = dDirX + dPlaneX * cameraX;
    float rayDirY = dDirY + dPlaneY * cameraX;
    
    int mapX = int(dPosX);
    int mapY = int(dPosY);
    
    float sideDistX;
    float sideDistY;
    
    float deltaDistX = (rayDirX == 0) ? 1e30 : abs(1 / rayDirX);
    float deltaDistY = (rayDirY == 0) ? 1e30 : abs(1 / rayDirY);
    float perpWallDist;
    
    int stepX;
    int stepY;
    
    int hit = 0; 
    int side; 
    
    if(rayDirX < 0) {
      stepX = -1;
      sideDistX = (dPosX - mapX) * deltaDistX;
    } else {
      stepX = 1;
      sideDistX = (mapX + 1.0 - dPosX) * deltaDistX;
    }
    if(rayDirY < 0) {
      stepY = -1;
      sideDistY = (dPosY - mapY) * deltaDistY;
    } else {
      stepY = 1;
      sideDistY = (mapY + 1.0 - dPosY) * deltaDistY;
    }
    
    while (hit == 0) {
      if(sideDistX < sideDistY) {
        sideDistX += deltaDistX;
        mapX += stepX;
        side = 0;
      } else {
        sideDistY += deltaDistY;
        mapY += stepY;
        side = 1;
      }
      
      if(mapX >= 0 && mapX < MAP_WIDTH && mapY >= 0 && mapY < MAP_HEIGHT) {
        if(DOOM_MAP[mapY][mapX] > 0) hit = 1;
      } else {
        hit = 1; 
      }
    }
    
    if(side == 0) perpWallDist = (sideDistX - deltaDistX);
    else          perpWallDist = (sideDistY - deltaDistY);
    
    int h = 64;
    int lineHeight = (int)(h / perpWallDist);
    
    int drawStart = -lineHeight / 2 + h / 2;
    if(drawStart < 0) drawStart = 0;
    int drawEnd = lineHeight / 2 + h / 2;
    if(drawEnd >= h) drawEnd = h - 1;
    
    // Simple black/white shading via dither or lines
    // On monochrome, we can draw a vertical line for the wall
    // If it's `side == 1`, we can add a gap to "shade" it.
    if(side == 1 && (x % 2 == 0)) {
        // Pseudo-shading
    } else {
        display.drawLine(x, drawStart, x, drawEnd, 1);
    }
  }

  // Draw Gun
  display.fillRect(60, 40, 8, 24, 1);
  display.fillRect(58, 55, 12, 9, 1);

  // Draw UI HUD Dashboard
  display.fillRect(0, 54, 128, 10, 0); // Clear background for HUD
  display.drawLine(0, 53, 128, 53, 1); // HUD top border
  display.setTextSize(1);
  display.setTextColor(1);
  
  display.setCursor(2, 55);
  display.print("AMMO 50");
  
  display.setCursor(55, 55);
  display.print("100%");
  
  display.setCursor(95, 55);
  display.print("ARMR 0");

  display.display();

  // Controls Handling - Use `stable == LOW` for continuous holding instead of single clicks
  float moveSpeed = 0.15f;
  float rotSpeed = 0.15f;

  if (bUp.stable == LOW) { // Walk Forward
    if(DOOM_MAP[int(dPosY)][int(dPosX + dDirX * moveSpeed * 1.5)] == 0) dPosX += dDirX * moveSpeed;
    if(DOOM_MAP[int(dPosY + dDirY * moveSpeed * 1.5)][int(dPosX)] == 0) dPosY += dDirY * moveSpeed;
  }
  if (bDown.stable == LOW) { // Walk Backward
    if(DOOM_MAP[int(dPosY)][int(dPosX - dDirX * moveSpeed * 1.5)] == 0) dPosX -= dDirX * moveSpeed;
    if(DOOM_MAP[int(dPosY - dDirY * moveSpeed * 1.5)][int(dPosX)] == 0) dPosY -= dDirY * moveSpeed;
  }
  if (bConfirm.stable == LOW) { // Turn Right
    float oldDirX = dDirX;
    dDirX = dDirX * cos(-rotSpeed) - dDirY * sin(-rotSpeed);
    dDirY = oldDirX * sin(-rotSpeed) + dDirY * cos(-rotSpeed);
    float oldPlaneX = dPlaneX;
    dPlaneX = dPlaneX * cos(-rotSpeed) - dPlaneY * sin(-rotSpeed);
    dPlaneY = oldPlaneX * sin(-rotSpeed) + dPlaneY * cos(-rotSpeed);
  }
  if (bEnter.stable == LOW) { // Turn Left
    float oldDirX = dDirX;
    dDirX = dDirX * cos(rotSpeed) - dDirY * sin(rotSpeed);
    dDirY = oldDirX * sin(rotSpeed) + dDirY * cos(rotSpeed);
    float oldPlaneX = dPlaneX;
    dPlaneX = dPlaneX * cos(rotSpeed) - dPlaneY * sin(rotSpeed);
    dPlaneY = oldPlaneX * sin(rotSpeed) + dPlaneY * cos(rotSpeed);
  }
}
