#pragma once

#include "globals.h"

// Sends a JSON command packet to the NEXUS desktop software
static void sendRemoteExec(const char* app_name, const char* args) {
    display.clearDisplay();
    drawHeader("NEXUS Remote");
    display.setCursor(0, 20); display.print("Trigger: "); display.print(app_name);
    display.display();
    
    char json_buf[256];
    snprintf(json_buf, sizeof(json_buf), 
             "{\"device_id\":\"OTOM-CORE\",\"source\":\"REMOTE\",\"command\":\"exec\",\"app\":\"%s\",\"args\":\"%s\",\"timestamp\":%lu}", 
             app_name, args, millis());
             
    Serial.println(json_buf);
    
    // Also try to send via TCP if WiFi is connected (future feature expansion)
    
    delay(1000);
}
