#pragma once

#include "globals.h"
#include <USB.h>
#include <USBHIDKeyboard.h>
#include <FS.h>
#include <SD.h>

USBHIDKeyboard Keyboard;
static bool badUsbInitialized = false;

static void executeDuckyScript(const char* filepath) {
  if (!badUsbInitialized) {
    USB.begin();
    Keyboard.begin();
    badUsbInitialized = true;
    delay(1000); 
  }
  
  display.clearDisplay();
  drawHeader("BadUSB Active");
  display.setTextColor(1);
  display.setCursor(0, 20); display.print("Exec: "); display.print(filepath);
  display.display();
  
  File f = SD.open(filepath);
  if (!f) {
    display.setCursor(0, 40); display.print("Error: File not found");
    display.display();
    delay(2000);
    return;
  }
  
  while(f.available()) {
     String line = f.readStringUntil('\n');
     line.trim();
     if(line.length() == 0 || line.startsWith("REM ")) continue;
     
     if (line.startsWith("STRING ")) {
         Keyboard.print(line.substring(7));
     } else if (line.startsWith("DELAY ")) {
         delay(line.substring(6).toInt());
     } else {
         // Advanced Key Parsing
         // Example: GUI r, CTRL ALT DELETE, SHIFT ENTER
         int startIdx = 0;
         while(startIdx < line.length()) {
             int spaceIdx = line.indexOf(' ', startIdx);
             if (spaceIdx == -1) spaceIdx = line.length();
             String keyStr = line.substring(startIdx, spaceIdx);
             keyStr.toUpperCase();
             
             if (keyStr == "ENTER") Keyboard.press(KEY_RETURN);
             else if (keyStr == "GUI" || keyStr == "WINDOWS") Keyboard.press(KEY_LEFT_GUI);
             else if (keyStr == "SHIFT") Keyboard.press(KEY_LEFT_SHIFT);
             else if (keyStr == "CTRL" || keyStr == "CONTROL") Keyboard.press(KEY_LEFT_CTRL);
             else if (keyStr == "ALT") Keyboard.press(KEY_LEFT_ALT);
             else if (keyStr == "TAB") Keyboard.press(KEY_TAB);
             else if (keyStr == "SPACE") Keyboard.press(' ');
             else if (keyStr == "UPARROW" || keyStr == "UP") Keyboard.press(KEY_UP_ARROW);
             else if (keyStr == "DOWNARROW" || keyStr == "DOWN") Keyboard.press(KEY_DOWN_ARROW);
             else if (keyStr == "LEFTARROW" || keyStr == "LEFT") Keyboard.press(KEY_LEFT_ARROW);
             else if (keyStr == "RIGHTARROW" || keyStr == "RIGHT") Keyboard.press(KEY_RIGHT_ARROW);
             else if (keyStr == "ESCAPE" || keyStr == "ESC") Keyboard.press(KEY_ESC);
             else if (keyStr == "CAPSLOCK") Keyboard.press(KEY_CAPS_LOCK);
             else if (keyStr == "DELETE" || keyStr == "DEL") Keyboard.press(KEY_DELETE);
             else if (keyStr == "F1") Keyboard.press(KEY_F1);
             else if (keyStr == "F2") Keyboard.press(KEY_F2);
             else if (keyStr == "F3") Keyboard.press(KEY_F3);
             else if (keyStr == "F4") Keyboard.press(KEY_F4);
             else if (keyStr == "F5") Keyboard.press(KEY_F5);
             else if (keyStr == "F10") Keyboard.press(KEY_F10);
             else if (keyStr == "F11") Keyboard.press(KEY_F11);
             else if (keyStr == "F12") Keyboard.press(KEY_F12);
             else if (keyStr.length() == 1) {
                 // Single character like 'r' in "GUI r"
                 char c = line.charAt(startIdx); 
                 Keyboard.press(c);
             }
             startIdx = spaceIdx + 1;
         }
         
         delay(25); // Small hold
         Keyboard.releaseAll();
     }
     delay(50); // Inter-instruction delay
  }
  f.close();
  
  display.setCursor(0, 40); display.print("Payload Complete!");
  display.display();
  delay(1500);
}

static void startBadUSB() {
  // Let's implement a mini file-browser blocking loop inside here to pick a payload
  File root = SD.open("/payloads");
  if (!root) {
      display.clearDisplay();
      drawHeader("BadUSB Explorer");
      display.setCursor(0, 20); display.print("No /payloads folder!");
      display.display();
      delay(2000);
      return;
  }
  
  String payloads[20];
  int pCount = 0;
  
  File file = root.openNextFile();
  while(file && pCount < 20){
      if(!file.isDirectory()){
          payloads[pCount] = String(file.name());
          pCount++;
      }
      file = root.openNextFile();
  }
  
  if (pCount == 0) {
      display.clearDisplay();
      drawHeader("BadUSB Explorer");
      display.setCursor(0, 20); display.print("No files found!");
      display.display();
      delay(2000);
      return;
  }
  
  int pIndex = 0;
  while(true) {
      display.clearDisplay();
      drawHeader("Select Payload");
      
      for(int i=0; i<min(4, pCount); i++) {
          int displayIdx = pIndex - (pIndex % 4) + i;
          if (displayIdx >= pCount) break;
          
          if (displayIdx == pIndex) {
              display.fillRect(0, 16 + (i*12), 128, 12, 1);
              display.setTextColor(0);
          } else {
              display.setTextColor(1);
          }
          display.setCursor(2, 18 + (i*12)); 
          display.print(payloads[displayIdx]);
      }
      display.display();
      
      updateButtons(millis());
      if (bUp.pressedEvent) {
          pIndex = (pIndex - 1 + pCount) % pCount;
      } else if (bDown.pressedEvent) {
          pIndex = (pIndex + 1) % pCount;
      } else if (bEnter.pressedEvent) {
          String fullPath = "/payloads/" + payloads[pIndex];
          executeDuckyScript(fullPath.c_str());
          break; // Return to previous menu after execution
      } else if (bExit.pressedEvent) {
          break; // Cancel
      }
      delay(20);
  }
}
