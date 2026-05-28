from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from PyQt6.QtCore import QObject, QThread, pyqtSignal
from PyQt6.QtWidgets import QFileDialog

from nexus.ai.ai_connector import AIConnector
from nexus.ai.chat_connector import ChatConnector
from nexus.db.database import DatabaseManager
from nexus.hardware.job_protocol import JOB_SCHEMA_VERSION, validate_job_payload
from nexus.hardware.telemetry_ingest import TelemetryIngestManager
from nexus.notes.notes_service import NotesService
from nexus.ui.main_window import MainWindow


def summarize_pcap_capture(file_path: str) -> str:
    path = Path(file_path)
    if not path.exists():
        return "Capture file not found"

    try:
        import pyshark
    except ImportError:
        return "pyshark is not installed. Run `pip install pyshark` to enable PCAP analysis."

    size_bytes = path.stat().st_size
    suffix = path.suffix.lower()

    lines = [
        f"File: {path.name}",
        f"Type: {suffix or 'unknown'}",
        f"Size: {size_bytes} bytes",
        "--- Processing PCAP with PyShark ---",
    ]

    try:
        cap = pyshark.FileCapture(str(path), keep_packets=False)
        packet_count = 0
        protocols: dict[str, int] = {}
        top_talkers: dict[str, int] = {}
        max_packets = 1000

        for pkt in cap:
            packet_count += 1

            highest_layer = pkt.highest_layer
            protocols[highest_layer] = protocols.get(highest_layer, 0) + 1

            if hasattr(pkt, "ip"):
                src = pkt.ip.src
                dst = pkt.ip.dst
                top_talkers[src] = top_talkers.get(src, 0) + 1
                top_talkers[dst] = top_talkers.get(dst, 0) + 1
            elif hasattr(pkt, "ipv6"):
                src = pkt.ipv6.src
                dst = pkt.ipv6.dst
                top_talkers[src] = top_talkers.get(src, 0) + 1
                top_talkers[dst] = top_talkers.get(dst, 0) + 1

            if packet_count >= max_packets:
                lines.append(f"[Note: Analysis capped at first {max_packets} packets for speed]")
                break

        cap.close()
        lines.append(f"Total packets scanned: {packet_count}")

        if protocols:
            lines.append("")
            lines.append("Top Protocols:")
            for proto, count in sorted(protocols.items(), key=lambda item: item[1], reverse=True)[:5]:
                lines.append(f"  - {proto}: {count} packets")

        if top_talkers:
            lines.append("")
            lines.append("Top Talkers (IP/IPv6):")
            for ip, count in sorted(top_talkers.items(), key=lambda item: item[1], reverse=True)[:5]:
                lines.append(f"  - {ip}: {count} appearances")

    except Exception as exc:
        lines.append(f"Error reading capture with pyshark: {exc}")

    return "\n".join(lines)


class PcapSummaryWorker(QThread):
    finished_signal = pyqtSignal(str, str)
    error_signal = pyqtSignal(str)

    def __init__(self, file_path: str) -> None:
        super().__init__()
        self.file_path = file_path

    def run(self) -> None:
        try:
            summary = summarize_pcap_capture(self.file_path)
            self.finished_signal.emit(self.file_path, summary)
        except Exception as exc:
            self.error_signal.emit(f"Failed to analyze capture: {exc}")


class AppController(QObject):
    def __init__(
        self,
        window: MainWindow,
        database: DatabaseManager,
        ingest: TelemetryIngestManager,
        ai_connector: AIConnector,
        chat_connector: ChatConnector,
        notes_service: NotesService,
    ) -> None:
        super().__init__()
        self.window = window
        self.db = database
        self.ingest = ingest
        self.ai = ai_connector
        self.chat = chat_connector
        self.notes_service = notes_service
        self._last_telemetry: dict[str, Any] = {}
        self._pcap_worker: PcapSummaryWorker | None = None
        self._pending_hardware_jobs: list[dict[str, Any]] = []

        self._bind_events()
        self._load_initial_state()

    def _bind_events(self) -> None:
        ingest_tab = self.window.ingest_tab
        ingest_tab.serial_start_btn.clicked.connect(self._start_serial_listener)
        ingest_tab.serial_stop_btn.clicked.connect(self.ingest.stop_serial)
        ingest_tab.tcp_start_btn.clicked.connect(self._start_tcp_listener)
        ingest_tab.tcp_stop_btn.clicked.connect(self.ingest.stop_tcp)

        self.ingest.raw_line_received.connect(self._on_raw_line)
        self.ingest.telemetry_received.connect(self._on_telemetry)
        self.ingest.telemetry_invalid.connect(self._on_invalid_telemetry)
        self.ingest.connection_state.connect(self._on_connection_state)

        self.window.ai_tab.analyze_btn.clicked.connect(self._on_run_ai)
        self.window.ai_tab.cancel_btn.clicked.connect(self.ai.cancel)
        self.window.ai_tab.dispatch_jobs_btn.clicked.connect(self._dispatch_hardware_jobs)
        self.ai.analysis_started.connect(lambda: self.window.ai_tab.set_status("Running analysis...", "warn"))
        self.ai.analysis_ready.connect(self._on_ai_ready)
        self.ai.analysis_error.connect(self._on_ai_error)

        self.window.logs_tab.refresh_btn.clicked.connect(self.refresh_logs)
        self.window.logs_tab.export_csv_btn.clicked.connect(self._export_logs_csv)
        self.window.logs_tab.purge_btn.clicked.connect(self._purge_logs)

        self.window.notes_tab.save_note_btn.clicked.connect(self._save_note)
        self.window.notes_tab.export_md_btn.clicked.connect(self._export_note_markdown)
        self.window.notes_tab.export_pdf_btn.clicked.connect(self._export_note_pdf)

        self.window.pentest_tab.load_pcap_btn.clicked.connect(self._load_pcap)
        self.window.pentest_tab.save_evidence_btn.clicked.connect(self._save_evidence_tag)

        # AI Chat bindings
        self.window.chat_tab.send_message_signal.connect(self.chat.send_message)
        self.window.chat_tab.clear_chat_signal.connect(self.chat.clear_history)
        self.chat.thinking_started.connect(lambda: self.window.chat_tab.set_thinking(True))
        self.chat.message_received.connect(self._on_chat_received)
        self.chat.error_occurred.connect(self._on_chat_error)

    def shutdown(self) -> None:
        self.ingest.stop_all()

    def _load_initial_state(self) -> None:
        # Auto-purge if DB has grown very large
        total = self.db.count_telemetry()
        if total > 100_000:
            self.db.purge_old_telemetry(keep_last_n=50_000)
            self.db.purge_old_anomalies(keep_last_n=10_000)

        self.refresh_network_views()
        self.refresh_logs()
        self.refresh_notes()
        self.window.update_status_bar(model=self.ai.model)

        anomalies = self.db.fetch_anomalies(limit=100)
        for anomaly in reversed(anomalies):
            text = (
                f"{anomaly.get('timestamp')} | {anomaly.get('event_type')} "
                f"({anomaly.get('severity')}): {anomaly.get('details')}"
            )
            self.window.incident_tab.add_anomaly(text)

        recent = self.db.fetch_telemetry(limit=1)
        if recent:
            self._last_telemetry = recent[0]["payload"]
            self.window.ai_tab.input_view.setPlainText(
                json.dumps(self._last_telemetry, ensure_ascii=True, indent=2)
            )

    def _start_serial_listener(self) -> None:
        port = self.window.ingest_tab.serial_port_input.text().strip()
        baud_text = self.window.ingest_tab.serial_baud_input.text().strip()
        try:
            baudrate = int(baud_text) if baud_text else 115200
        except ValueError:
            self.window.ingest_tab.set_status("Invalid baud value", ok=False)
            return

        self.window.ingest_tab.set_status("Starting serial listener...", ok=None)
        self.ingest.start_serial(port=port, baudrate=baudrate)

    def _start_tcp_listener(self) -> None:
        host = self.window.ingest_tab.tcp_host_input.text().strip() or "0.0.0.0"
        port_text = self.window.ingest_tab.tcp_port_input.text().strip()
        try:
            port = int(port_text) if port_text else 9000
        except ValueError:
            self.window.ingest_tab.set_status("Invalid TCP port", ok=False)
            return

        self.window.ingest_tab.set_status("Starting TCP listener...", ok=None)
        self.ingest.start_tcp(host=host, port=port)

    def _on_connection_state(self, channel: str, connected: bool, message: str) -> None:
        self.window.dashboard_tab.update_connection(channel, connected, message)
        self.window.ingest_tab.set_status(f"[{channel}] {message}", ok=connected)
        self.window.dashboard_tab.append_channel_activity(f"{channel.upper()}: {message}")
        if channel == "serial":
            self.window.ingest_tab.set_serial_running(connected)
            self.window.update_status_bar(serial_connected=connected, serial_msg=message)
        else:
            self.window.ingest_tab.set_tcp_running(connected)
            self.window.update_status_bar(tcp_connected=connected, tcp_msg=message)

    def _on_raw_line(self, line: str) -> None:
        self.window.ingest_tab.append_raw_line(line)
        self.window.dashboard_tab.append_channel_activity(line)

    def _on_telemetry(self, telemetry: dict[str, Any]) -> None:
        self._last_telemetry = telemetry
        self.window.ingest_tab.show_parsed(telemetry)
        self.window.dashboard_tab.append_telemetry_preview(telemetry)

        stamp = str(telemetry.get("timestamp", ""))
        device_id = str(telemetry.get("device_id", "unknown-device"))
        source = str(telemetry.get("source", "unknown"))
        self.window.incident_tab.add_timeline_event(f"{stamp} | {device_id} via {source}")

        if not self.window.ai_tab.input_view.toPlainText().strip():
            self.window.ai_tab.input_view.setPlainText(json.dumps(telemetry, ensure_ascii=True, indent=2))

        self._maybe_log_anomaly(telemetry)
        self.refresh_network_views()
        self.refresh_logs()
        self.window.notes_tab.refresh_timestamp()



    def _maybe_log_anomaly(self, telemetry: dict[str, Any]) -> None:
        metrics = telemetry.get("metrics", {})
        anomaly_score = 0.0
        if isinstance(metrics, dict):
            try:
                anomaly_score = float(metrics.get("anomaly_score", 0.0))
            except (TypeError, ValueError):
                anomaly_score = 0.0

        if telemetry.get("anomaly") or anomaly_score >= 0.8:
            details = f"Device={telemetry.get('device_id')} anomaly_score={anomaly_score:.2f}"
            self.db.store_anomaly(event_type="telemetry_anomaly", severity="high", details=details)
            self.window.incident_tab.add_anomaly(details)

    def _on_invalid_telemetry(self, message: str) -> None:
        self.window.ingest_tab.set_status(message, ok=False)
        self.window.incident_tab.add_anomaly(message)
        self.db.store_anomaly(event_type="ingest_error", severity="medium", details=message)

    def _on_run_ai(self) -> None:
        text = self.window.ai_tab.input_view.toPlainText().strip()
        if text:
            try:
                payload = json.loads(text)
                if not isinstance(payload, dict):
                    payload = {"input": payload}
            except json.JSONDecodeError:
                payload = {"raw_text": text}
        elif self._last_telemetry:
            payload = self._last_telemetry
        else:
            self.window.ai_tab.set_status("No telemetry available for AI analysis", "bad")
            return

        self.ai.analyze(payload)

    def _on_ai_ready(self, result: dict[str, Any]) -> None:
        self.window.ai_tab.set_result(result)
        self.window.ai_tab.set_status("Analysis complete", "ok")
        self._pending_hardware_jobs = []
        for raw_job in result.get("hardware_jobs", []):
            if isinstance(raw_job, dict):
                ok, reason = validate_job_payload(raw_job)
                if ok:
                    self._pending_hardware_jobs.append(raw_job)
                else:
                    self.window.incident_tab.add_anomaly(f"Rejected AI job suggestion: {reason}")

        event_id = self.window.notes_tab.event_id_input.text().strip() or str(
            self._last_telemetry.get("device_id", "")
        )
        telemetry_id = self._last_telemetry.get("_db_id")
        self.db.store_ai_analysis(
            telemetry_id=int(telemetry_id) if isinstance(telemetry_id, int) else None,
            event_id=event_id,
            threat_classification=str(result.get("threat_classification", "Unknown")),
            severity=str(result.get("severity", "medium")),
            mitigation=str(result.get("suggested_mitigation", "")),
            raw_response=result.get("raw_response", {}),
        )
        self.window.incident_tab.add_timeline_event("AI analysis completed")
        if self._pending_hardware_jobs:
            self.window.ai_tab.set_status(
                f"Analysis complete; {len(self._pending_hardware_jobs)} hardware job(s) ready",
                "ok",
            )

    def _on_ai_error(self, message: str) -> None:
        self.window.ai_tab.set_status(message, "bad")
        self.window.incident_tab.add_anomaly(message)
        self.db.store_anomaly(event_type="ai_error", severity="medium", details=message)

    def _dispatch_hardware_jobs(self) -> None:
        if not self._pending_hardware_jobs:
            self.window.ai_tab.set_status("No approved hardware jobs to dispatch", "bad")
            return

        if not self.ingest.has_serial_command_channel():
            self.window.ai_tab.set_status("Serial command channel is not available", "bad")
            return

        delivered = 0
        for job in self._pending_hardware_jobs:
            payload = dict(job)
            payload.setdefault("schema", JOB_SCHEMA_VERSION)
            payload.setdefault("kind", "job_submit")
            payload.setdefault("requested_by", "nexus-ai")
            payload.setdefault("audit_mode", True)
            line = json.dumps(payload, ensure_ascii=True)
            if self.ingest.send_serial_command(line):
                delivered += 1
                self.db.store_anomaly(
                    event_type="job_dispatch",
                    severity="low",
                    details=f"Dispatched {payload.get('job_type')} job {payload.get('job_id')}",
                )
                self.window.incident_tab.add_timeline_event(
                    f"Dispatched hardware job {payload.get('job_type')} ({payload.get('job_id')})"
                )
            else:
                self.db.store_anomaly(
                    event_type="job_dispatch_error",
                    severity="medium",
                    details=f"Failed to send job {payload.get('job_id')}",
                )

        self._pending_hardware_jobs = []
        self.window.ai_tab.dispatch_jobs_btn.setEnabled(False)
        self.window.ai_tab.set_status(f"Dispatched {delivered} hardware job(s)", "ok" if delivered else "bad")

    def _on_chat_received(self, response: str) -> None:
        self.window.chat_tab.add_message(response, "ai")
        self.window.chat_tab.set_thinking(False)
        self.window.incident_tab.add_timeline_event("AI chat message received")

    def _on_chat_error(self, message: str) -> None:
        self.window.chat_tab.add_message(f"Error: {message}", "ai")
        self.window.chat_tab.set_thinking(False)
        self.window.incident_tab.add_anomaly(f"AI Chat Error: {message}")

    def refresh_network_views(self) -> None:
        devices = self.db.fetch_device_summary()
        total_events = self.db.count_telemetry()
        last_device = str(self._last_telemetry.get("device_id", "")) if self._last_telemetry else ""
        if not last_device and devices:
            last_device = str(devices[0].get("device_id", ""))

        self.window.network_tab.update_devices(devices)
        self.window.dashboard_tab.update_environment_summary(
            total_events=total_events,
            total_devices=len(devices),
            last_device=last_device,
        )
        self.window.update_status_bar(db_rows=total_events)

    def refresh_logs(self) -> None:
        device_filter = self.window.logs_tab.device_filter_input.text().strip()
        limit = int(self.window.logs_tab.limit_spin.value())
        rows = self.db.fetch_telemetry(device_id=device_filter, limit=limit)
        self.window.logs_tab.populate_logs(rows)
        self.window.logs_tab.set_status(f"Loaded {len(rows)} rows", ok=True)

    def _export_logs_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self.window,
            "Export Logs as CSV",
            "nexus_logs.csv",
            "CSV Files (*.csv)",
        )
        if not path:
            return
        try:
            self.window.logs_tab.export_to_csv(path)
            self.window.logs_tab.set_status(f"Exported: {Path(path).name}", ok=True)
        except Exception as exc:
            self.window.logs_tab.set_status(f"Export failed: {exc}", ok=False)

    def _purge_logs(self) -> None:
        from PyQt6.QtWidgets import QMessageBox
        total = self.db.count_telemetry()
        reply = QMessageBox.warning(
            self.window,
            "Purge Old Telemetry",
            f"This will delete all but the 50,000 most recent rows.\n"
            f"Current row count: {total:,}\n\nProceed?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        deleted_t = self.db.purge_old_telemetry(keep_last_n=50_000)
        deleted_a = self.db.purge_old_anomalies(keep_last_n=10_000)
        self.refresh_logs()
        self.window.logs_tab.set_status(
            f"Purged {deleted_t:,} telemetry rows and {deleted_a:,} anomaly rows", ok=True
        )


    def refresh_notes(self) -> None:
        notes = self.notes_service.recent_notes(limit=100)
        self.window.notes_tab.populate_notes(notes)

    def _save_note(self) -> None:
        event_id = self.window.notes_tab.event_id_input.text().strip()
        if not event_id:
            event_id = str(self._last_telemetry.get("device_id", ""))

        content = self.window.notes_tab.markdown().strip()
        if not content:
            self.window.notes_tab.set_status("Note content is empty", ok=False)
            return

        note_id = self.notes_service.save_note(event_id=event_id, markdown_content=content)
        self.window.notes_tab.set_status(f"Saved note #{note_id}", ok=True)
        self.window.notes_tab.refresh_timestamp()
        self.refresh_notes()

    def _export_note_markdown(self) -> None:
        content = self.window.notes_tab.markdown().strip()
        if not content:
            self.window.notes_tab.set_status("No content to export", ok=False)
            return

        path, _ = QFileDialog.getSaveFileName(
            self.window,
            "Export Notes as Markdown",
            "nexus_notes.md",
            "Markdown (*.md)",
        )
        if not path:
            return

        self.notes_service.export_markdown(path, content)
        self.window.notes_tab.set_status(f"Exported Markdown: {Path(path).name}", ok=True)

    def _export_note_pdf(self) -> None:
        content = self.window.notes_tab.markdown().strip()
        if not content:
            self.window.notes_tab.set_status("No content to export", ok=False)
            return

        path, _ = QFileDialog.getSaveFileName(
            self.window,
            "Export Notes as PDF",
            "nexus_notes.pdf",
            "PDF (*.pdf)",
        )
        if not path:
            return

        self.notes_service.export_pdf(path, content, title="NEXUS Incident Notes")
        self.window.notes_tab.set_status(f"Exported PDF: {Path(path).name}", ok=True)

    def _load_pcap(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self.window,
            "Open PCAP",
            "",
            "Capture Files (*.pcap *.pcapng);;All Files (*)",
        )
        if not file_path:
            return

        if self._pcap_worker is not None and self._pcap_worker.isRunning():
            self.window.pentest_tab.set_status("PCAP analysis already running", ok=False)
            return

        self.window.pentest_tab.set_status("Analyzing capture...", ok=True)
        self.window.pentest_tab.show_pcap_summary(path=Path(file_path).name, summary="Loading...")

        worker = PcapSummaryWorker(file_path)
        worker.finished_signal.connect(self._on_pcap_summary_ready)
        worker.error_signal.connect(self._on_pcap_summary_error)
        worker.finished.connect(worker.deleteLater)
        self._pcap_worker = worker
        worker.start()

    def _on_pcap_summary_ready(self, file_path: str, summary: str) -> None:
        self.window.pentest_tab.show_pcap_summary(path=Path(file_path).name, summary=summary)
        self.window.pentest_tab.set_status("PCAP analysis complete", ok=True)
        self.window.incident_tab.add_timeline_event(f"Loaded capture: {Path(file_path).name}")
        self._pcap_worker = None

    def _on_pcap_summary_error(self, message: str) -> None:
        self.window.pentest_tab.set_status(message, ok=False)
        self._pcap_worker = None

    def _save_evidence_tag(self) -> None:
        event_id = self.window.pentest_tab.event_id_input.text().strip()
        tags = self.window.pentest_tab.tags_input.text().strip()
        description = self.window.pentest_tab.description_input.text().strip()

        if not tags:
            self.window.pentest_tab.set_status("Tags are required", ok=False)
            return

        record_id = self.db.store_evidence_tag(event_id=event_id, tags=tags, description=description)
        self.window.pentest_tab.set_status(f"Saved evidence tag #{record_id}", ok=True)
