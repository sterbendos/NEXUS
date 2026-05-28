#pragma once

#include "globals.h"

static const char* JOB_SCHEMA = "nexus.remote.job.v1";
static const uint8_t JOB_QUEUE_SIZE = 4;
static const uint16_t JOB_ARG_LIMIT = 96;

struct RemoteJob {
  char jobId[24];
  char jobType[24];
  char requestedBy[24];
  char arguments[JOB_ARG_LIMIT];
  bool auditMode;
  bool valid;
};

static RemoteJob jobQueue[JOB_QUEUE_SIZE];
static uint8_t jobHead = 0;
static uint8_t jobCount = 0;
static bool auditModeArmed = false;
static bool activeJobRunning = false;
static bool activeJobBlocking = false;
static char activeJobId[24] = "";
static char activeJobType[24] = "";
static char activeJobRequestedBy[24] = "";
static uint32_t activeJobStartedMs = 0;
static char serialCommandBuffer[256];
static uint16_t serialCommandBufferLen = 0;
static char tcpCommandBuffers[3][256];
static uint16_t tcpCommandBufferLens[3] = {0, 0, 0};

static bool commandContainsKey(const String& line, const char* key, String& valueOut) {
  const String needle = String("\"") + key + "\"";
  int keyPos = line.indexOf(needle);
  if (keyPos < 0) return false;
  int colonPos = line.indexOf(':', keyPos);
  if (colonPos < 0) return false;
  int firstQuote = line.indexOf('"', colonPos + 1);
  if (firstQuote < 0) return false;
  int secondQuote = line.indexOf('"', firstQuote + 1);
  if (secondQuote < 0) return false;
  valueOut = line.substring(firstQuote + 1, secondQuote);
  return true;
}

static bool commandContainsBool(const String& line, const char* key, bool& valueOut) {
  const String needle = String("\"") + key + "\"";
  int keyPos = line.indexOf(needle);
  if (keyPos < 0) return false;
  int colonPos = line.indexOf(':', keyPos);
  if (colonPos < 0) return false;
  String tail = line.substring(colonPos + 1);
  tail.trim();
  if (tail.startsWith("true")) {
    valueOut = true;
    return true;
  }
  if (tail.startsWith("false")) {
    valueOut = false;
    return true;
  }
  return false;
}

static bool isAllowlistedJobType(const char* jobType) {
  if (!jobType || !jobType[0]) return false;
  const char* allowed[] = {
    "device_inventory",
    "hardware_self_test",
    "passive_survey",
    "config_check",
    "benign_validation",
    "spectrum_scan",
    "link_test",
    "capture_signal",
    "monitor_mode",
    "sd_benchmark",
  };
  for (uint8_t i = 0; i < sizeof(allowed) / sizeof(allowed[0]); i++) {
    if (strcmp(jobType, allowed[i]) == 0) return true;
  }
  return false;
}

static void emitJobTelemetry(
  const char* eventType,
  const char* jobId,
  const char* jobType,
  const char* requestedBy,
  const char* status,
  const char* summary,
  const char* severity = "info"
) {
  char ipText[16];
  char macText[18];
  telemetryGetIp(ipText, sizeof(ipText));
  telemetryGetMac(macText, sizeof(macText));

  auto writeLine = [&](Print& out) {
    out.print("{\"schema\":\"");
    out.print(JOB_SCHEMA);
    out.print("\",\"kind\":\"job_status\"");
    out.print(",\"timestamp\":\"");
    out.print((unsigned long)millis());
    out.print("\",\"device_id\":\"");
    jsonEscapedPrint(out, telemetryDeviceId);
    out.print("\",\"source\":\"esp32-firmware\"");
    out.print(",\"channel\":\"remote-job\"");
    out.print(",\"event_type\":\"");
    jsonEscapedPrint(out, eventType);
    out.print("\",\"severity\":\"");
    jsonEscapedPrint(out, severity);
    out.print("\",\"message\":\"");
    jsonEscapedPrint(out, summary);
    out.print("\",\"network\":{\"ip\":\"");
    jsonEscapedPrint(out, ipText);
    out.print("\",\"mac\":\"");
    jsonEscapedPrint(out, macText);
    out.print("\"}");
    out.print(",\"job\":{\"id\":\"");
    jsonEscapedPrint(out, jobId);
    out.print("\",\"type\":\"");
    jsonEscapedPrint(out, jobType);
    out.print("\",\"status\":\"");
    jsonEscapedPrint(out, status);
    out.print("\",\"requested_by\":\"");
    jsonEscapedPrint(out, requestedBy);
    out.print("\"}}");
    out.println();
  };

  writeLine(Serial);
  for (uint8_t i = 0; i < 3; i++) {
    if (telemetryClients[i] && telemetryClients[i].connected()) {
      writeLine(telemetryClients[i]);
    }
  }
}

static void emitJobBlocked(const char* jobId, const char* jobType, const char* reason, const char* requestedBy = "") {
  emitJobTelemetry("job_blocked", jobId, jobType, requestedBy, "blocked", reason, "warn");
}

static void emitJobAccepted(const char* jobId, const char* jobType, const char* requestedBy) {
  emitJobTelemetry("job_queued", jobId, jobType, requestedBy, "queued", "Job accepted and queued", "info");
}

static void emitJobRunning(const char* jobId, const char* jobType, const char* requestedBy) {
  emitJobTelemetry("job_running", jobId, jobType, requestedBy, "running", "Job started", "info");
}

static void emitJobCompleted(const char* jobId, const char* jobType, const char* summary, const char* requestedBy = "") {
  emitJobTelemetry("job_completed", jobId, jobType, requestedBy, "completed", summary, "info");
}

static void emitJobFailed(const char* jobId, const char* jobType, const char* summary, const char* requestedBy = "") {
  emitJobTelemetry("job_failed", jobId, jobType, requestedBy, "failed", summary, "warn");
}

static void queueJob(const RemoteJob& job) {
  if (jobCount >= JOB_QUEUE_SIZE) {
    emitJobBlocked(job.jobId, job.jobType, "Job queue is full", job.requestedBy);
    return;
  }
  uint8_t slot = (jobHead + jobCount) % JOB_QUEUE_SIZE;
  jobQueue[slot] = job;
  jobQueue[slot].valid = true;
  jobCount++;
  emitJobAccepted(job.jobId, job.jobType, job.requestedBy);
}

static bool dequeueJob(RemoteJob& outJob) {
  if (jobCount == 0) return false;
  outJob = jobQueue[jobHead];
  jobQueue[jobHead].valid = false;
  jobHead = (jobHead + 1) % JOB_QUEUE_SIZE;
  jobCount--;
  return true;
}

static void finishActiveJob(const char* summary, bool success = true) {
  if (!activeJobRunning) return;
  if (success) emitJobCompleted(activeJobId, activeJobType, summary, activeJobRequestedBy);
  else emitJobFailed(activeJobId, activeJobType, summary, activeJobRequestedBy);
  activeJobRunning = false;
  activeJobBlocking = false;
  activeJobId[0] = 0;
  activeJobType[0] = 0;
  activeJobRequestedBy[0] = 0;
}

static void startNonBlockingJob(const RemoteJob& job) {
  if (strcmp(job.jobType, "device_inventory") == 0) {
    char summary[128];
    snprintf(summary, sizeof(summary), "device=%s sd=%d nrf1=%d nrf2=%d", telemetryDeviceId, sdReady, nrf1Ready, nrf2Ready);
    emitJobCompleted(job.jobId, job.jobType, summary, job.requestedBy);
    return;
  }
  if (strcmp(job.jobType, "hardware_self_test") == 0) {
    refreshStatus();
    char summary[128];
    snprintf(summary, sizeof(summary), "status sd=%d nrf1=%d nrf2=%d", sdReady, nrf1Ready, nrf2Ready);
    emitJobCompleted(job.jobId, job.jobType, summary, job.requestedBy);
    return;
  }
  if (strcmp(job.jobType, "passive_survey") == 0 || strcmp(job.jobType, "config_check") == 0 || strcmp(job.jobType, "benign_validation") == 0) {
    char summary[160];
    snprintf(summary, sizeof(summary), "survey menu=%d page=%d run=%d capture=%u wifi=%u", menuIndex, page, runMode, (unsigned)capturedCount, (unsigned)wifiCount);
    emitJobCompleted(job.jobId, job.jobType, summary, job.requestedBy);
    return;
  }

  // Active job families
  activeJobRunning = true;
  activeJobBlocking = true;
  strncpy(activeJobId, job.jobId, sizeof(activeJobId) - 1);
  strncpy(activeJobType, job.jobType, sizeof(activeJobType) - 1);
  strncpy(activeJobRequestedBy, job.requestedBy, sizeof(activeJobRequestedBy) - 1);
  activeJobId[sizeof(activeJobId) - 1] = 0;
  activeJobType[sizeof(activeJobType) - 1] = 0;
  activeJobRequestedBy[sizeof(activeJobRequestedBy) - 1] = 0;
  activeJobStartedMs = millis();
  emitJobRunning(job.jobId, job.jobType, job.requestedBy);

  if (strcmp(job.jobType, "spectrum_scan") == 0) startSpectrumScan();
  else if (strcmp(job.jobType, "link_test") == 0) startLinkTest();
  else if (strcmp(job.jobType, "capture_signal") == 0) startCapture();
  else if (strcmp(job.jobType, "monitor_mode") == 0) startMonitor();
  else if (strcmp(job.jobType, "sd_benchmark") == 0) {
    runSdBenchOnce();
    finishActiveJob("SD benchmark completed");
    return;
  }
  else finishActiveJob("Unknown active job type", false);
}

static void maybeProcessQueuedJobs() {
  if (activeJobRunning) {
    if (activeJobBlocking && activeJobStartedMs > 0 && (millis() - activeJobStartedMs) > 300000UL) {
      runMode = RUN_NONE;
      finishActiveJob("Job timed out", false);
      return;
    }
    if (runMode == RUN_NONE) {
      finishActiveJob("Active job finished");
    }
    return;
  }

  RemoteJob next;
  if (dequeueJob(next)) {
    startNonBlockingJob(next);
  }
}

static void handleRemoteCommandLine(const String& line) {
  if (line.indexOf(JOB_SCHEMA) < 0) return;

  String kind;
  if (!commandContainsKey(line, "kind", kind)) return;

  if (kind == "job_arm") {
    bool armed = false;
    commandContainsBool(line, "audit_mode", armed);
    auditModeArmed = armed;
    emitTelemetry("job_arm", "info", armed ? "Audit mode armed" : "Audit mode disarmed");
    return;
  }

  if (kind == "job_submit") {
    RemoteJob job;
    memset(&job, 0, sizeof(job));
    job.valid = true;
    job.auditMode = true;
    String tmp;
    if (!commandContainsKey(line, "job_id", tmp)) { emitJobBlocked("", "", "Missing job_id"); return; }
    tmp.toCharArray(job.jobId, sizeof(job.jobId));
    if (!commandContainsKey(line, "job_type", tmp)) { emitJobBlocked(job.jobId, "", "Missing job_type", job.requestedBy); return; }
    tmp.toCharArray(job.jobType, sizeof(job.jobType));
    if (commandContainsKey(line, "requested_by", tmp)) tmp.toCharArray(job.requestedBy, sizeof(job.requestedBy));
    else strncpy(job.requestedBy, "nexus-ai", sizeof(job.requestedBy) - 1);
    if (!commandContainsBool(line, "audit_mode", job.auditMode)) job.auditMode = false;
    commandContainsKey(line, "arguments", tmp);
    tmp.toCharArray(job.arguments, sizeof(job.arguments));

    if (!isAllowlistedJobType(job.jobType)) {
      emitJobBlocked(job.jobId, job.jobType, "Job type is not allowlisted", job.requestedBy);
      return;
    }
    if (!(auditModeArmed || job.auditMode)) {
      emitJobBlocked(job.jobId, job.jobType, "Audit mode is not armed", job.requestedBy);
      return;
    }
    queueJob(job);
    return;
  }
}

static void pollSerialRemoteCommands() {
  while (Serial.available() > 0) {
    char c = (char)Serial.read();
    if (c == '\n') {
      serialCommandBuffer[serialCommandBufferLen] = 0;
      String line(serialCommandBuffer);
      line.trim();
      if (line.length() > 0) handleRemoteCommandLine(line);
      serialCommandBufferLen = 0;
      serialCommandBuffer[0] = 0;
      continue;
    }
    if (c == '\r') continue;
    if (serialCommandBufferLen < sizeof(serialCommandBuffer) - 1) {
      serialCommandBuffer[serialCommandBufferLen++] = c;
    } else {
      serialCommandBufferLen = 0;
      serialCommandBuffer[0] = 0;
    }
  }
}

static void pollTcpRemoteCommands() {
  for (uint8_t i = 0; i < 3; i++) {
    WiFiClient& client = telemetryClients[i];
    if (!client || !client.connected()) {
      tcpCommandBufferLens[i] = 0;
      tcpCommandBuffers[i][0] = 0;
      continue;
    }

    while (client.available() > 0) {
      char c = (char)client.read();
      if (c == '\n') {
        tcpCommandBuffers[i][tcpCommandBufferLens[i]] = 0;
        String line(tcpCommandBuffers[i]);
        line.trim();
        if (line.length() > 0) handleRemoteCommandLine(line);
        tcpCommandBufferLens[i] = 0;
        tcpCommandBuffers[i][0] = 0;
        continue;
      }
      if (c == '\r') continue;
      if (tcpCommandBufferLens[i] < sizeof(tcpCommandBuffers[i]) - 1) {
        tcpCommandBuffers[i][tcpCommandBufferLens[i]++] = c;
      } else {
        tcpCommandBufferLens[i] = 0;
        tcpCommandBuffers[i][0] = 0;
      }
    }
  }
}

static void jobControlTick() {
  pollSerialRemoteCommands();
  pollTcpRemoteCommands();
  maybeProcessQueuedJobs();
}
