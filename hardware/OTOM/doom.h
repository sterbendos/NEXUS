#pragma once

#include "globals.h"
#include <math.h>

#define MAP_WIDTH 8
#define MAP_HEIGHT 8

// 0: empty, 1: wall, 2: ammo, 3: health, 4: goal, 5: breakable wall
static uint8_t DOOM_MAP[MAP_HEIGHT][MAP_WIDTH] = {
  {1,1,1,1,1,1,1,1},
  {1,0,2,0,0,3,0,1},
  {1,0,1,5,1,1,0,1},
  {1,0,1,0,0,1,0,1},
  {1,0,5,0,0,0,0,1},
  {1,0,1,1,0,2,4,1},
  {1,0,0,0,0,0,0,1},
  {1,1,1,1,1,1,1,1}
};

static uint8_t orig_map[MAP_HEIGHT][MAP_WIDTH];

static float dPosX = 2.0f;
static float dPosY = 2.0f;
static float dDirX = -1.0f;
static float dDirY = 0.0f;
static float dPlaneX = 0.0f;
static float dPlaneY = 0.66f;

static int playerHealth = 100;
static int playerAmmo = 10;
static int playerArmor = 0;
static bool levelComplete = false;
static int flashFrames = 0;

static void resetMap() {
    uint8_t template_map[8][8] = {
      {1,1,1,1,1,1,1,1},
      {1,0,2,0,0,3,0,1},
      {1,0,1,5,1,1,0,1},
      {1,0,1,0,0,1,0,1},
      {1,0,5,0,0,0,0,1},
      {1,0,1,1,0,2,4,1},
      {1,0,0,0,0,0,0,1},
      {1,1,1,1,1,1,1,1}
    };
    memcpy(DOOM_MAP, template_map, sizeof(template_map));
}

static void startDoom() {
  resetMap();
  dPosX = 1.5f;
  dPosY = 1.5f;
  dDirX = 0.0f;
  dDirY = 1.0f;
  dPlaneX = 0.66f;
  dPlaneY = 0.0f;
  
  playerHealth = 100;
  playerAmmo = 10;
  levelComplete = false;
  flashFrames = 0;

  runMode = RUN_DOOM;
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(1);
  display.setCursor(20, 20);
  display.print("E1M1: Loading...");
  display.display();
  delay(1000);
}

static void doomShoot() {
  if (playerAmmo <= 0) return;
  playerAmmo--;
  flashFrames = 3; 

  // Raycast to find the first wall hit by the gunshot
  float rayX = dPosX;
  float rayY = dPosY;
  float step = 0.2f;
  for (int i=0; i<30; i++) {
    rayX += dDirX * step;
    rayY += dDirY * step;
    int mX = (int)rayX;
    int mY = (int)rayY;

    if (DOOM_MAP[mY][mX] == 5) { // Hit breakable wall
      DOOM_MAP[mY][mX] = 0; // Destroy wall
      break;
    } else if (DOOM_MAP[mY][mX] == 1) { // Hit solid wall
      break;
    }
  }
}

static void doomStep() {
  display.clearDisplay();
  
  if (levelComplete) {
    display.setTextSize(2);
    display.setCursor(10, 20);
    display.print("LEVEL");
    display.setCursor(10, 40);
    display.print("COMPLETE!");
    display.display();
    
    if (bExit.stable == LOW || bEnter.stable == LOW) {
      runMode = RUN_NONE;
      uiMode = UI_MENU;
      page = PAGE_NONE;
      drawMenu();
    }
    return;
  }
  
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
    int hitType = 0;
    
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
        uint8_t val = DOOM_MAP[mapY][mapX];
        if(val == 1 || val == 5 || val == 4) { 
           hit = 1; 
           hitType = val;
        }
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
    if(drawEnd >= 54) drawEnd = 53; // stop at HUD
    
    if (hitType == 5) { // Breakable wall
       if (x%2==0) display.drawLine(x, drawStart, x, drawEnd, 1);
    } else if (hitType == 4) { // Goal
       if (x%3==0) display.drawLine(x, drawStart, x, drawEnd, 1);
    } else { // Standard solid
      display.drawLine(x, drawStart, x, drawEnd, 1);
    }
  }

  // Draw Gun (Animating if firing)
  if (flashFrames > 0) {
    display.fillCircle(64, 30, 10 + flashFrames, 1); // muzzle flash
    display.fillRect(60, 45, 8, 24, 1);
    display.fillRect(58, 60, 12, 9, 1);
    flashFrames--;
  } else {
    display.fillRect(60, 40, 8, 24, 1);
    display.fillRect(58, 55, 12, 9, 1);
  }

  // Draw HUD
  display.fillRect(0, 54, 128, 10, 0);
  display.drawLine(0, 53, 128, 53, 1);
  display.setTextSize(1);
  display.setTextColor(1);
  
  display.setCursor(2, 55); display.print("A:"); display.print(playerAmmo);
  display.setCursor(45, 55); display.print(playerHealth); display.print("%");
  display.setCursor(95, 55); display.print("R:"); display.print(playerArmor);

  display.display();

  // Control Inputs
  float moveSpeed = 0.12f;
  float rotSpeed = 0.12f;

  if (bUp.stable == LOW) { // Walk Forward
    float nx = dPosX + dDirX * moveSpeed * 1.5;
    float ny = dPosY + dDirY * moveSpeed * 1.5;
    if(DOOM_MAP[(int)dPosY][(int)nx] < 1) dPosX += dDirX * moveSpeed;
    if(DOOM_MAP[(int)ny][(int)dPosX] < 1) dPosY += dDirY * moveSpeed;
  }
  if (bDown.stable == LOW) { // Walk Backward
    float nx = dPosX - dDirX * moveSpeed * 1.5;
    float ny = dPosY - dDirY * moveSpeed * 1.5;
    if(DOOM_MAP[(int)dPosY][(int)nx] < 1) dPosX -= dDirX * moveSpeed;
    if(DOOM_MAP[(int)ny][(int)dPosX] < 1) dPosY -= dDirY * moveSpeed;
  }
  if (bConfirm.stable == LOW) { // Turn Right
    float oldDirX = dDirX;
    dDirX = dDirX * cos(-rotSpeed) - dDirY * sin(-rotSpeed);
    dDirY = oldDirX * sin(-rotSpeed) + dDirY * cos(-rotSpeed);
    float oldPlaneX = dPlaneX;
    dPlaneX = dPlaneX * cos(-rotSpeed) - dPlaneY * sin(-rotSpeed);
    dPlaneY = oldPlaneX * sin(-rotSpeed) + dPlaneY * cos(-rotSpeed);
  }
  if (bEnter.stable == LOW) { // Shoot
     // We need to rate limit shooting so it doesn't spray infinitely
     static uint32_t lastShot = 0;
     if (millis() - lastShot > 300) {
       doomShoot();
       lastShot = millis();
     }
  }
  
  // Turn Left using combination or a secondary button if available
  // Wait, OTOM has UP, DOWN, ENTER, EXIT, CONFIRM. 
  // Let's make EXIT = Turn Left, and Hold UP+EXIT to actually Quit tool?
  // Let's use bExit for Turn Left, but if bExit and bDown are held we quit?
  // Actually, let's keep bExit for turning left and use a menu double-click to exit, or just use another combo.
  if (bExit.stable == LOW) { // Turn Left
    float oldDirX = dDirX;
    dDirX = dDirX * cos(rotSpeed) - dDirY * sin(rotSpeed);
    dDirY = oldDirX * sin(rotSpeed) + dDirY * cos(rotSpeed);
    float oldPlaneX = dPlaneX;
    dPlaneX = dPlaneX * cos(rotSpeed) - dPlaneY * sin(rotSpeed);
    dPlaneY = oldPlaneX * sin(rotSpeed) + dPlaneY * cos(rotSpeed);
  }

  // Collectibles Logic
  int pX = (int)dPosX;
  int pY = (int)dPosY;
  if (DOOM_MAP[pY][pX] == 2) { 
      playerAmmo += 10;
      DOOM_MAP[pY][pX] = 0;
  }
  if (DOOM_MAP[pY][pX] == 3) {
      playerHealth += 25;
      if (playerHealth > 100) playerHealth = 100;
      DOOM_MAP[pY][pX] = 0;
  }
  if (DOOM_MAP[pY][pX] == 4) {
      levelComplete = true; // Touched goal
  }

  // To quit, hold ENTER + EXIT?
  if (bEnter.stable == LOW && bExit.stable == LOW) {
      runMode = RUN_NONE;
      uiMode = UI_MENU;
      page = PAGE_NONE;
      drawMenu();
  }
}
