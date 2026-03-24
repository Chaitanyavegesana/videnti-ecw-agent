/**
 * Videnti eCW Bridge — Popup Script
 *
 * Handles the popup UI: shows WebSocket status, frame type,
 * and provides buttons to manually trigger data extraction.
 */

"use strict";

// ─── DOM refs ─────────────────────────────────────────────────────────────────

const statusBadge      = document.getElementById("statusBadge");
const statusText       = document.getElementById("statusText");
const frameTypeEl      = document.getElementById("frameType");
const btnExtractChart  = document.getElementById("btnExtractChart");
const btnExtractSched  = document.getElementById("btnExtractSchedule");
const logEl            = document.getElementById("log");

// ─── Helpers ──────────────────────────────────────────────────────────────────

function addLog(msg, type = "info") {
  const entry = document.createElement("div");
  entry.className = `log-entry ${type}`;
  entry.textContent = `[${new Date().toLocaleTimeString()}] ${msg}`;
  logEl.prepend(entry);
  // Trim log to 30 entries
  while (logEl.children.length > 30) logEl.removeChild(logEl.lastChild);
}

function setStatus(status) {
  statusBadge.className = `badge ${status}`;
  const labels = { connected: "Connected", disconnected: "Disconnected", error: "Error" };
  statusText.textContent = labels[status] || status;

  const isConnected = status === "connected";
  btnExtractChart.disabled = !isConnected;
  btnExtractSched.disabled = !isConnected;
}

// ─── Load Persisted State ──────────────────────────────────────────────────────

async function refreshUI() {
  const data = await chrome.storage.session.get([
    "wsStatus", "lastFrameType", "lastFrameUrl",
  ]);
  setStatus(data.wsStatus || "disconnected");
  frameTypeEl.textContent = data.lastFrameType || "—";
}

// ─── Background Messages ───────────────────────────────────────────────────────

chrome.runtime.onMessage.addListener((message) => {
  if (message.type === "status_update") {
    setStatus(message.status);
    addLog(`Connection: ${message.status}`, message.status === "connected" ? "ok" : "err");
  }
  if (message.type === "pend_order_request") {
    addLog(`Order request: CPT ${message.payload.cpt_code}`, "info");
  }
});

// ─── Buttons ──────────────────────────────────────────────────────────────────

btnExtractChart.addEventListener("click", async () => {
  btnExtractChart.disabled = true;
  addLog("Extracting chart data…", "info");

  try {
    const resp = await chrome.runtime.sendMessage({ action: "extract_chart_now" });
    if (resp && resp.ok) {
      addLog("Chart data sent to ICS backend", "ok");
    } else {
      addLog(`Extract failed: ${resp?.error || "unknown"}`, "err");
    }
  } catch (e) {
    addLog(`Error: ${e.message}`, "err");
  } finally {
    btnExtractChart.disabled = false;
  }
});

btnExtractSched.addEventListener("click", async () => {
  btnExtractSched.disabled = true;
  addLog("Extracting schedule…", "info");

  try {
    const resp = await chrome.runtime.sendMessage({ action: "extract_schedule_now" });
    if (resp && resp.ok) {
      addLog("Schedule data sent to ICS backend", "ok");
    } else {
      addLog(`Extract failed: ${resp?.error || "unknown"}`, "err");
    }
  } catch (e) {
    addLog(`Error: ${e.message}`, "err");
  } finally {
    btnExtractSched.disabled = false;
  }
});

// ─── Init ─────────────────────────────────────────────────────────────────────

refreshUI();
