(() => {
  const STORAGE_KEY = "nexus-demo-state-v1";
  const JOB_SCHEMA = "nexus.remote.job.v1";
  const JOB_LIMIT = 4;

  const jobsCatalog = {
    device_inventory: "Device inventory snapshot",
    hardware_self_test: "Hardware self-test",
    passive_survey: "Passive survey",
    config_check: "Configuration check",
    benign_validation: "Benign validation",
    sd_benchmark: "SD benchmark",
  };

  const scenarioLibrary = {
    steady: [
      { event_type: "heartbeat", severity: "info", message: "Periodic status pulse", anomaly: false },
      {
        event_type: "device_inventory",
        severity: "info",
        message: "Inventory snapshot updated",
        anomaly: false,
      },
      {
        event_type: "passive_survey",
        severity: "info",
        message: "Passive survey returned a clean baseline",
        anomaly: false,
      },
      {
        event_type: "config_check",
        severity: "info",
        message: "Configuration hash matches the expected profile",
        anomaly: false,
      },
    ],
    noisy: [
      { event_type: "heartbeat", severity: "info", message: "Heartbeat received over TCP", anomaly: false },
      {
        event_type: "telemetry_anomaly",
        severity: "medium",
        message: "Unexpected jitter in the sample cadence",
        anomaly: true,
      },
      {
        event_type: "ingest_error",
        severity: "medium",
        message: "One malformed record was normalized by ingest",
        anomaly: true,
      },
      {
        event_type: "passive_survey",
        severity: "info",
        message: "Passive survey remains healthy",
        anomaly: false,
      },
    ],
    maintenance: [
      {
        event_type: "hardware_self_test",
        severity: "info",
        message: "Display, SD, and radio readiness confirmed",
        anomaly: false,
      },
      {
        event_type: "sd_benchmark",
        severity: "info",
        message: "SD benchmark completed in demo mode",
        anomaly: false,
      },
      {
        event_type: "device_inventory",
        severity: "info",
        message: "Inventory job ready for dispatch",
        anomaly: false,
      },
    ],
    anomaly: [
      {
        event_type: "telemetry_anomaly",
        severity: "high",
        message: "Anomaly score crossed the threshold",
        anomaly: true,
      },
      {
        event_type: "job_blocked",
        severity: "warn",
        message: "Audit mode is not armed",
        anomaly: true,
      },
      {
        event_type: "ingest_error",
        severity: "medium",
        message: "Malformed JSON was safely normalized",
        anomaly: true,
      },
    ],
  };

  const els = {
    startButton: document.getElementById("start-button"),
    pauseButton: document.getElementById("pause-button"),
    pulseButton: document.getElementById("pulse-button"),
    scenarioSelect: document.getElementById("scenario-select"),
    transportSelect: document.getElementById("transport-select"),
    jobSelect: document.getElementById("job-select"),
    auditSwitch: document.getElementById("audit-switch"),
    jobButton: document.getElementById("job-button"),
    resetButton: document.getElementById("reset-button"),
    streamState: document.getElementById("stream-state"),
    transportState: document.getElementById("transport-state"),
    rowsState: document.getElementById("rows-state"),
    telemetryCount: document.getElementById("telemetry-count"),
    anomalyCount: document.getElementById("anomaly-count"),
    deviceId: document.getElementById("device-id"),
    lastSeen: document.getElementById("last-seen"),
    screenTransport: document.getElementById("screen-transport"),
    deviceScreen: document.getElementById("device-screen"),
    classification: document.getElementById("classification"),
    severity: document.getElementById("severity"),
    mitigation: document.getElementById("mitigation"),
    rationale: document.getElementById("rationale"),
    analysisJson: document.getElementById("analysis-json"),
    recommendations: document.getElementById("recommendations"),
    analysisBadge: document.getElementById("analysis-badge"),
    feedList: document.getElementById("feed-list"),
    jobList: document.getElementById("job-list"),
    stages: Array.from(document.querySelectorAll(".stage")),
  };

  const state = {
    running: true,
    scenario: "steady",
    transport: "serial",
    auditArmed: true,
    deviceId: createDeviceId(),
    sequence: 0,
    telemetryCount: 0,
    anomalyCount: 0,
    dbRows: 0,
    deviceCount: 1,
    lastSeen: "",
    events: [],
    jobs: [],
    activeStage: "firmware",
    analysis: makeDefaultAnalysis(),
    tick: 0,
  };

  let intervalId = null;

  function makeDefaultAnalysis() {
    return {
      model: "gemma3:4b",
      threat_classification: "Stable baseline",
      severity: "low",
      suggested_mitigation: "Continue passive monitoring and keep audit mode armed only for intentional lab tests.",
      rationale: "The stream is stable, the queue is empty, and the ingest pipeline is behaving as expected.",
      hardware_jobs: [
        {
          job_id: "demo-job-0001",
          job_type: "device_inventory",
          requested_by: "demo-ui",
          audit_mode: true,
          arguments: { source: "simulation" },
        },
      ],
    };
  }

  function createDeviceId() {
    const tail = Math.floor(Math.random() * 0xffffff)
      .toString(16)
      .toUpperCase()
      .padStart(6, "0");
    return `OTOM-${tail}`;
  }

  function pad(num) {
    return String(num).padStart(2, "0");
  }

  function formatClock(date = new Date()) {
    return `${pad(date.getHours())}:${pad(date.getMinutes())}:${pad(date.getSeconds())}`;
  }

  function createMac() {
    const seed = state.deviceId.replace("OTOM-", "");
    const lastOctet = ((state.sequence * 17) % 255).toString(16).padStart(2, "0").toUpperCase();
    return `24:6F:${seed.slice(0, 2)}:${seed.slice(2, 4)}:${seed.slice(4, 6)}:${lastOctet}`;
  }

  function createIp() {
    const octet = 20 + (state.sequence % 60);
    return `192.168.4.${octet}`;
  }

  function createTelemetry(template) {
    const now = new Date();
    const anomalyScore = template.anomaly ? 0.82 + (state.sequence % 5) * 0.03 : template.severity === "medium" ? 0.48 : 0.08;
    const pageCycle = ["status", "spectrum", "monitor", "sd", "session", "nfc"];
    const runCycle = ["none", "monitor", "capture", "none", "spectrum", "none"];
    const uiPage = pageCycle[state.sequence % pageCycle.length];
    const runMode = template.event_type.startsWith("job_")
      ? "none"
      : runCycle[state.sequence % runCycle.length];

    return {
      timestamp: now.toISOString(),
      device_id: state.deviceId,
      source: "esp32-firmware",
      channel: state.transport,
      event_id: String(state.sequence + 1),
      event_type: template.event_type,
      severity: template.severity,
      message: template.message,
      anomaly: Boolean(template.anomaly || anomalyScore >= 0.8),
      network: {
        ip: createIp(),
        mac: createMac(),
      },
      metrics: {
        sd_ready: 1,
        nrf1_ready: 1,
        nrf2_ready: state.scenario === "maintenance" ? 0 : 1,
        session_on: state.running ? 1 : 0,
        captured_count: 4 + state.telemetryCount * 2 + (state.scenario === "maintenance" ? 1 : 0),
        wifi_count: 2 + (state.scenario === "noisy" ? 12 : 3) + (state.sequence % 4),
        file_count: 1 + (state.scenario === "maintenance" ? 3 : 0),
        menu_index: state.sequence % 8,
        anomaly_score: Number(anomalyScore.toFixed(2)),
      },
      events: [{ name: template.event_type, message: template.message }],
      state: {
        ui_mode: "page",
        page: uiPage,
        run_mode: runMode,
      },
    };
  }

  function queueTelemetry(template) {
    const telemetry = createTelemetry(template);
    state.sequence += 1;
    state.telemetryCount += 1;
    state.dbRows += 1;
    state.lastSeen = telemetry.timestamp;
    if (telemetry.anomaly || telemetry.metrics.anomaly_score >= 0.8) {
      state.anomalyCount += 1;
    }

    state.events.unshift(telemetry);
    state.events = state.events.slice(0, 18);
    state.activeStage = pickStageForEvent(telemetry);
    state.analysis = deriveAnalysis(telemetry);

    render();
    persist();
  }

  function pickStageForEvent(telemetry) {
    if (telemetry.event_type.startsWith("job_")) {
      return "firmware";
    }
    if (telemetry.anomaly || telemetry.metrics.anomaly_score >= 0.8) {
      return "ai";
    }
    if (telemetry.event_type === "sd_benchmark" || telemetry.event_type === "config_check") {
      return "sqlite";
    }
    if (telemetry.channel === "tcp") {
      return "transport";
    }
    return ["firmware", "transport", "ingest", "sqlite"][state.sequence % 4];
  }

  function deriveAnalysis(telemetry) {
    const anomalyScore = Number(telemetry.metrics.anomaly_score || 0);
    const baseJobs = [
      {
        job_id: `demo-job-${String(state.sequence + 1).padStart(4, "0")}`,
        job_type: "device_inventory",
        requested_by: "demo-ui",
        audit_mode: true,
        arguments: { source: "simulation", reason: "baseline snapshot" },
      },
    ];

    if (telemetry.anomaly || anomalyScore >= 0.8) {
      return {
        model: "gemma3:4b",
        threat_classification: "Telemetry anomaly",
        severity: anomalyScore >= 0.9 ? "critical" : "high",
        suggested_mitigation:
          "Inspect the ingest path, verify RF noise sources in the lab, and keep audit mode armed before dispatching any follow-up job.",
        rationale:
          "The most recent telemetry carries an elevated anomaly score or explicit anomaly flag, so the desktop should treat the stream as suspicious until reviewed.",
        hardware_jobs: [
          {
            job_id: `demo-job-${String(state.sequence + 1).padStart(4, "0")}`,
            job_type: "hardware_self_test",
            requested_by: "demo-ui",
            audit_mode: true,
            arguments: { focus: "display-sd-radio" },
          },
          {
            job_id: `demo-job-${String(state.sequence + 2).padStart(4, "0")}`,
            job_type: "passive_survey",
            requested_by: "demo-ui",
            audit_mode: true,
            arguments: { scope: "monitor-only" },
          },
        ],
      };
    }

    if (telemetry.event_type === "sd_benchmark" || state.scenario === "maintenance") {
      return {
        model: "gemma3:4b",
        threat_classification: "Maintenance activity",
        severity: "low",
        suggested_mitigation:
          "Document the maintenance window, keep the stream open, and store the resulting notes alongside the telemetry record.",
        rationale:
          "The simulated device is in a maintenance-oriented scenario and the stream is showing normal lab activity rather than a threat condition.",
        hardware_jobs: [
          {
            job_id: `demo-job-${String(state.sequence + 1).padStart(4, "0")}`,
            job_type: "hardware_self_test",
            requested_by: "demo-ui",
            audit_mode: true,
            arguments: { reason: "maintenance window" },
          },
          {
            job_id: `demo-job-${String(state.sequence + 2).padStart(4, "0")}`,
            job_type: "config_check",
            requested_by: "demo-ui",
            audit_mode: true,
            arguments: { reason: "baseline audit" },
          },
        ],
      };
    }

    if (state.scenario === "noisy") {
      return {
        model: "gemma3:4b",
        threat_classification: "Noisy telemetry stream",
        severity: "medium",
        suggested_mitigation:
          "Continue passive monitoring, confirm the transport channel, and use a single allowlisted job to confirm the device is still healthy.",
        rationale:
          "The stream is stable but has intermittent jitter, so a cautious response is appropriate before escalating.",
        hardware_jobs: [
          {
            job_id: `demo-job-${String(state.sequence + 1).padStart(4, "0")}`,
            job_type: "passive_survey",
            requested_by: "demo-ui",
            audit_mode: true,
            arguments: { reason: "noise review" },
          },
          {
            job_id: `demo-job-${String(state.sequence + 2).padStart(4, "0")}`,
            job_type: "device_inventory",
            requested_by: "demo-ui",
            audit_mode: true,
            arguments: { reason: "confirm state" },
          },
        ],
      };
    }

    return {
      model: "gemma3:4b",
      threat_classification: "Stable baseline",
      severity: "low",
      suggested_mitigation:
        "Continue passive monitoring and keep audit mode armed only for intentional test runs.",
      rationale:
        "The latest telemetry matches the expected baseline and there is no active alert condition.",
      hardware_jobs: baseJobs,
    };
  }

  function buildTelemetryTemplate() {
    const list = scenarioLibrary[state.scenario] || scenarioLibrary.steady;
    const index = state.tick % list.length;
    state.tick += 1;
    return list[index];
  }

  function seedDemo() {
    if (state.events.length > 0) {
      return;
    }

    queueTelemetry({
      event_type: "boot",
      severity: "info",
      message: "Firmware ready and telemetry output initialized",
      anomaly: false,
    });
    queueTelemetry({
      event_type: "heartbeat",
      severity: "info",
      message: "Periodic status pulse",
      anomaly: false,
    });
    queueTelemetry({
      event_type: "config_check",
      severity: "info",
      message: "Configuration baseline verified",
      anomaly: false,
    });
  }

  function updateScreen() {
    const latest = state.events[0];
    const transport = state.transport.toUpperCase();
    const page = latest ? latest.state.page : "status";
    const runMode = latest ? latest.state.run_mode : "none";
    const lastEvent = latest ? latest.event_type : "boot";
    const anomalyScore = latest ? latest.metrics.anomaly_score.toFixed(2) : "0.00";

    els.deviceScreen.textContent = [
      `OTOM / NEXUS`,
      `device: ${state.deviceId}`,
      `transport: ${transport}`,
      `ui_mode: page`,
      `page: ${page}`,
      `run_mode: ${runMode}`,
      `last_event: ${lastEvent}`,
      `queue_depth: ${activeQueueDepth()}`,
      `audit_mode: ${state.auditArmed ? "armed" : "disarmed"}`,
      `anomaly_score: ${anomalyScore}`,
    ].join("\n");
  }

  function activeQueueDepth() {
    return state.jobs.filter((job) => job.status === "queued" || job.status === "running").length;
  }

  function renderStats() {
    els.streamState.textContent = state.running ? "Running" : "Paused";
    els.transportState.textContent = state.transport;
    els.rowsState.textContent = state.dbRows.toLocaleString();
    els.telemetryCount.textContent = state.telemetryCount.toLocaleString();
    els.anomalyCount.textContent = state.anomalyCount.toLocaleString();
    els.deviceId.textContent = state.deviceId;
    els.lastSeen.textContent = state.lastSeen ? formatClock(new Date(state.lastSeen)) : "-";
    els.screenTransport.textContent = state.transport;
    els.analysisBadge.textContent =
      state.analysis.severity === "low"
        ? "Stable baseline"
        : state.analysis.severity === "medium"
          ? "Review needed"
          : "Escalated";

    els.startButton.disabled = state.running;
    els.pauseButton.disabled = !state.running;
  }

  function renderAnalysis() {
    els.classification.textContent = state.analysis.threat_classification;
    els.severity.textContent = state.analysis.severity;
    els.mitigation.textContent = state.analysis.suggested_mitigation;
    els.rationale.textContent = state.analysis.rationale;
    els.analysisJson.textContent = JSON.stringify(state.analysis, null, 2);
    els.recommendations.innerHTML = "";

    state.analysis.hardware_jobs.forEach((job) => {
      const pill = document.createElement("span");
      pill.className = "chip";
      pill.textContent = job.job_type;
      els.recommendations.appendChild(pill);
    });

    document.body.classList.remove("severity-low", "severity-medium", "severity-high", "severity-critical");
    document.body.classList.add(`severity-${state.analysis.severity}`);
  }

  function renderFeed() {
    els.feedList.innerHTML = "";
    state.events.slice(0, 14).forEach((event) => {
      const item = document.createElement("article");
      item.className = `feed-item severity-${severityClass(event.severity)}`;
      item.innerHTML = `
        <div class="feed-top">
          <div class="feed-meta">
            <span class="chip subtle">${formatClock(new Date(event.timestamp))}</span>
            <span class="chip subtle">${event.channel}</span>
            <span class="chip ${event.anomaly ? "live" : "subtle"}">${event.severity}</span>
          </div>
        </div>
        <strong>${escapeHtml(event.event_type)}</strong>
        <p>${escapeHtml(event.message)}</p>
        <div class="feed-meta">
          <span class="muted">${escapeHtml(event.device_id)}</span>
          <span class="muted">score ${Number(event.metrics.anomaly_score || 0).toFixed(2)}</span>
        </div>
      `;
      els.feedList.appendChild(item);
    });
  }

  function renderJobs() {
    els.jobList.innerHTML = "";
    state.jobs.slice(0, 6).forEach((job) => {
      const card = document.createElement("article");
      card.className = `job-card severity-${severityClass(job.status === "blocked" ? "warn" : job.status === "completed" ? "info" : "medium")}`;
      const jsonPreview = {
        schema: JOB_SCHEMA,
        kind: "job_submit",
        job_id: job.job_id,
        job_type: job.job_type,
        requested_by: job.requested_by,
        audit_mode: job.audit_mode,
        arguments: job.arguments,
      };
      card.innerHTML = `
        <div class="job-card-head">
          <div>
            <span class="chip ${statusChipClass(job.status)}">${job.status}</span>
            <strong>${escapeHtml(job.job_type)}</strong>
          </div>
          <span class="chip subtle">${formatClock(new Date(job.created_at))}</span>
        </div>
        <p>${escapeHtml(job.summary)}</p>
        <div class="job-meta">
          <span class="muted">${escapeHtml(job.job_id)}</span>
          <span class="muted">requested by ${escapeHtml(job.requested_by)}</span>
        </div>
        <code>${escapeHtml(JSON.stringify(jsonPreview, null, 2))}</code>
      `;
      els.jobList.appendChild(card);
    });
  }

  function renderPipeline() {
    els.stages.forEach((stage) => {
      stage.classList.toggle("is-active", stage.dataset.stage === state.activeStage);
    });
  }

  function renderControls() {
    els.scenarioSelect.value = state.scenario;
    els.transportSelect.value = state.transport;
    els.jobSelect.value = els.jobSelect.value || "device_inventory";
    els.auditSwitch.checked = state.auditArmed;
  }

  function render() {
    renderControls();
    renderStats();
    renderAnalysis();
    renderFeed();
    renderJobs();
    renderPipeline();
    updateScreen();
  }

  function statusChipClass(status) {
    if (status === "completed") return "live";
    if (status === "running") return "accent";
    if (status === "blocked") return "subtle";
    return "subtle";
  }

  function severityClass(severity) {
    if (severity === "critical") return "critical";
    if (severity === "high" || severity === "warn") return "high";
    if (severity === "medium") return "medium";
    return "low";
  }

  function persist() {
    try {
      localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({
          running: state.running,
          scenario: state.scenario,
          transport: state.transport,
          auditArmed: state.auditArmed,
          deviceId: state.deviceId,
          sequence: state.sequence,
          telemetryCount: state.telemetryCount,
          anomalyCount: state.anomalyCount,
          dbRows: state.dbRows,
          deviceCount: state.deviceCount,
          lastSeen: state.lastSeen,
          events: state.events,
          jobs: state.jobs,
          activeStage: state.activeStage,
          analysis: state.analysis,
          tick: state.tick,
        })
      );
    } catch {
      // Ignore persistence failures in private browsing or locked-down contexts.
    }
  }

  function restore() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) {
        return;
      }
      const parsed = JSON.parse(raw);
      if (parsed && typeof parsed === "object") {
        Object.assign(state, {
          running: typeof parsed.running === "boolean" ? parsed.running : state.running,
          scenario: typeof parsed.scenario === "string" ? parsed.scenario : state.scenario,
          transport: typeof parsed.transport === "string" ? parsed.transport : state.transport,
          auditArmed: typeof parsed.auditArmed === "boolean" ? parsed.auditArmed : state.auditArmed,
          deviceId: typeof parsed.deviceId === "string" ? parsed.deviceId : state.deviceId,
          sequence: Number.isFinite(parsed.sequence) ? parsed.sequence : state.sequence,
          telemetryCount: Number.isFinite(parsed.telemetryCount) ? parsed.telemetryCount : state.telemetryCount,
          anomalyCount: Number.isFinite(parsed.anomalyCount) ? parsed.anomalyCount : state.anomalyCount,
          dbRows: Number.isFinite(parsed.dbRows) ? parsed.dbRows : state.dbRows,
          deviceCount: Number.isFinite(parsed.deviceCount) ? parsed.deviceCount : state.deviceCount,
          lastSeen: typeof parsed.lastSeen === "string" ? parsed.lastSeen : state.lastSeen,
          events: Array.isArray(parsed.events) ? parsed.events : state.events,
          jobs: Array.isArray(parsed.jobs) ? parsed.jobs : state.jobs,
          activeStage: typeof parsed.activeStage === "string" ? parsed.activeStage : state.activeStage,
          analysis: parsed.analysis && typeof parsed.analysis === "object" ? parsed.analysis : state.analysis,
          tick: Number.isFinite(parsed.tick) ? parsed.tick : state.tick,
        });
      }
    } catch {
      // Ignore malformed persistence data.
    }
  }

  function maybeStartTicker() {
    if (intervalId) {
      clearInterval(intervalId);
      intervalId = null;
    }

    if (!state.running) {
      return;
    }

    intervalId = setInterval(() => {
      if (!state.running) {
        return;
      }
      queueTelemetry(buildTelemetryTemplate());
    }, 2200);
  }

  function setRunning(running) {
    state.running = running;
    maybeStartTicker();
    render();
    persist();
  }

  function injectOneEvent() {
    queueTelemetry(buildTelemetryTemplate());
  }

  function queueJob() {
    const activeJobs = activeQueueDepth();
    const jobType = els.jobSelect.value;
    const now = new Date();
    const id = `demo-job-${String(state.sequence + state.jobs.length + 1).padStart(4, "0")}`;
    const job = {
      job_id: id,
      job_type: jobType,
      requested_by: "demo-ui",
      audit_mode: state.auditArmed,
      arguments: { scenario: state.scenario, transport: state.transport },
      status: "queued",
      summary: `${jobsCatalog[jobType]} queued for simulation`,
      created_at: now.toISOString(),
    };

    if (!state.auditArmed) {
      job.status = "blocked";
      job.summary = "Blocked because audit mode is disarmed";
      state.jobs.unshift(job);
      queueTelemetry({
        event_type: "job_blocked",
        severity: "warn",
        message: "Audit mode is disarmed, so the job stays blocked",
        anomaly: true,
      });
      render();
      persist();
      return;
    }

    if (activeJobs >= JOB_LIMIT) {
      job.status = "blocked";
      job.summary = "Blocked because the simulated queue is full";
      state.jobs.unshift(job);
      queueTelemetry({
        event_type: "job_blocked",
        severity: "warn",
        message: "The simulated job queue is full",
        anomaly: true,
      });
      render();
      persist();
      return;
    }

    state.jobs.unshift(job);
    queueTelemetry({
      event_type: "job_queued",
      severity: "info",
      message: `${jobType} accepted and added to the queue`,
      anomaly: false,
    });

    setTimeout(() => {
      const liveJob = state.jobs.find((item) => item.job_id === id);
      if (!liveJob || liveJob.status === "blocked") {
        return;
      }
      liveJob.status = "running";
      liveJob.summary = `${jobsCatalog[jobType]} is running`;
      queueTelemetry({
        event_type: "job_running",
        severity: "info",
        message: `${jobType} has started`,
        anomaly: false,
      });
      render();
      persist();
    }, 800);

    setTimeout(() => {
      const liveJob = state.jobs.find((item) => item.job_id === id);
      if (!liveJob || liveJob.status === "blocked") {
        return;
      }
      liveJob.status = "completed";
      liveJob.summary = `${jobsCatalog[jobType]} completed successfully`;
      queueTelemetry({
        event_type: "job_completed",
        severity: "info",
        message: `${jobType} completed successfully`,
        anomaly: false,
      });
      render();
      persist();
    }, 2000);
  }

  function resetDemo() {
    state.running = true;
    state.scenario = "steady";
    state.transport = "serial";
    state.auditArmed = true;
    state.sequence = 0;
    state.telemetryCount = 0;
    state.anomalyCount = 0;
    state.dbRows = 0;
    state.lastSeen = "";
    state.events = [];
    state.jobs = [];
    state.activeStage = "firmware";
    state.analysis = makeDefaultAnalysis();
    state.tick = 0;
    maybeStartTicker();
    seedDemo();
    render();
    persist();
  }

  function bindEvents() {
    els.startButton.addEventListener("click", () => setRunning(true));
    els.pauseButton.addEventListener("click", () => setRunning(false));
    els.pulseButton.addEventListener("click", injectOneEvent);
    els.scenarioSelect.addEventListener("change", (event) => {
      state.scenario = event.target.value;
      state.analysis = deriveAnalysis(state.events[0] || createTelemetry({
        event_type: "heartbeat",
        severity: "info",
        message: "Baseline refresh",
        anomaly: false,
      }));
      render();
      persist();
    });
    els.transportSelect.addEventListener("change", (event) => {
      state.transport = event.target.value;
      state.analysis = deriveAnalysis(state.events[0] || createTelemetry({
        event_type: "heartbeat",
        severity: "info",
        message: "Transport refresh",
        anomaly: false,
      }));
      render();
      persist();
    });
    els.jobButton.addEventListener("click", queueJob);
    els.auditSwitch.addEventListener("change", (event) => {
      state.auditArmed = event.target.checked;
      render();
      persist();
    });
    els.resetButton.addEventListener("click", resetDemo);
  }

  function escapeHtml(value) {
    return String(value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function boot() {
    restore();
    bindEvents();
    seedDemo();
    render();
    maybeStartTicker();
  }

  boot();
})();
