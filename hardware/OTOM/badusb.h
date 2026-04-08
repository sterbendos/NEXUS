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
     if(line.length() == 0) continue;
     
     if (line.startsWith("STRING ")) {
         Keyboard.print(line.substring(7));
     } else if (line.startsWith("DELAY ")) {
         delay(line.substring(6).toInt());
     } else if (line == "ENTER") {
         Keyboard.write(KEY_RETURN);
     } else if (line == "GUI r") {
         Keyboard.press(KEY_LEFT_GUI);
         Keyboard.press('r');
         delay(100);
         Keyboard.releaseAll();
     } else if (line == "TAB") {
         Keyboard.write(KEY_TAB);
     } else if (line == "UPARROW") {
         Keyboard.write(KEY_UP_ARROW);
     } else if (line == "DOWNARROW") {
         Keyboard.write(KEY_DOWN_ARROW);
     }
     delay(50); // Small inter-instruction delay
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
