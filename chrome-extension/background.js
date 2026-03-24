/**
 * Videnti eCW Bridge — Background Service Worker
 *
 * Coordinates communication between:
 *   - The content script running inside eCW page frames
 *   - The popup UI
 *   - The local ICS backend (ws://localhost:8001/ws/extension)
 *
 * Architecture:
 *   Content Script → (chrome.runtime.sendMessage) → Background Worker
 *   Background Worker → (WebSocket) → ICS eCW-Bridge Server (port 8001)
 *   Background Worker → (chrome.runtime.sendMessage) → Popup UI
 *
 * HIPAA Note:
 *   The WebSocket connects to localhost ONLY.  No data ever leaves the
 *   clinic workstation via this extension.
 */

"use strict";

const ICS_WS_URL = "ws://localhost:8001/ws/extension";
const RECONNECT_DELAY_MS = 3000;
const MAX_RECONNECT_ATTEMPTS = 10;
const RECONNECT_BACKOFF_MULTIPLIER = 1.5;
const PENDING_QUEUE_MAX = 50;

// ─── State ────────────────────────────────────────────────────────────────────

let ws = null;
let wsReady = false;
let reconnectAttempts = 0;
let pendingMessages = [];  // queued while WS is connecting

// ─── WebSocket Management ─────────────────────────────────────────────────────

function connectWebSocket() {
  if (ws && (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING)) {
    return;
  }

  console.log("[Videnti] Connecting to ICS backend at", ICS_WS_URL);
  ws = new WebSocket(ICS_WS_URL);

  ws.addEventListener("open", () => {
    console.log("[Videnti] WebSocket connected");
    wsReady = true;
    reconnectAttempts = 0;
    broadcastStatus("connected");

    // Flush any messages that arrived while we were connecting.
    while (pendingMessages.length > 0) {
      const msg = pendingMessages.shift();
      ws.send(JSON.stringify(msg));
    }
  });

  ws.addEventListener("message", (event) => {
    try {
      const data = JSON.parse(event.data);
      handleBackendMessage(data);
    } catch (e) {
      console.error("[Videnti] Failed to parse backend message:", e);
    }
  });

  ws.addEventListener("close", () => {
    console.warn("[Videnti] WebSocket closed");
    wsReady = false;
    broadcastStatus("disconnected");
    scheduleReconnect();
  });

  ws.addEventListener("error", (err) => {
    console.error("[Videnti] WebSocket error:", err);
    wsReady = false;
    broadcastStatus("error");
  });
}

function scheduleReconnect() {
  if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
    console.error("[Videnti] Max reconnect attempts reached. Give up.");
    return;
  }
  reconnectAttempts++;
  const delay = RECONNECT_DELAY_MS * Math.pow(RECONNECT_BACKOFF_MULTIPLIER, reconnectAttempts - 1);
  console.log(`[Videnti] Reconnecting in ${Math.round(delay)}ms (attempt ${reconnectAttempts})`);
  setTimeout(connectWebSocket, delay);
}

/**
 * Sends a payload to the ICS backend via WebSocket.
 * If the socket is not yet open, the message is queued.
 */
function sendToBackend(payload) {
  if (wsReady && ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify(payload));
  } else {
    // Cap the pending queue to prevent unbounded memory growth
    if (pendingMessages.length < PENDING_QUEUE_MAX) {
      pendingMessages.push(payload);
    } else {
      console.warn("[Videnti] Pending queue full; dropping oldest message");
      pendingMessages.shift();
      pendingMessages.push(payload);
    }
    connectWebSocket();  // Attempt (re)connect
  }
}

// ─── Backend → Extension Messages ────────────────────────────────────────────

/**
 * Handles commands sent FROM the ICS backend TO the extension.
 *
 * Supported commands:
 *   { type: "request_schedule" }        → triggers schedule extraction
 *   { type: "request_chart", mrn: "…" } → triggers chart extraction for MRN
 *   { type: "pend_order", … }           → broadcasts order-pend request to popup
 */
function handleBackendMessage(data) {
  switch (data.type) {
    case "request_schedule":
      extractScheduleFromActiveTab();
      break;

    case "request_chart":
      extractChartFromActiveTab(data.mrn);
      break;

    case "pend_order":
      // Forward to popup so the user can confirm before any action is taken.
      broadcastToPopup({ type: "pend_order_request", payload: data });
      break;

    case "ack":
      console.log("[Videnti] Backend ACK:", data.message || "ok");
      break;

    default:
      console.warn("[Videnti] Unknown backend message type:", data.type);
  }
}

// ─── Extract Schedule ─────────────────────────────────────────────────────────

async function extractScheduleFromActiveTab() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tabs.length) return;

  try {
    const results = await chrome.scripting.executeScript({
      target: { tabId: tabs[0].id, allFrames: true },
      func: () => {
        // Inline extraction in case content script isn't loaded yet.
        const rows = document.querySelectorAll(
          "tr.appt-row, tr[data-apptid], .appointmentRow, [class*='apptRow']"
        );
        return Array.from(rows).map((row) => ({
          mrn: row.getAttribute("data-mrn") || "",
          time: (row.querySelector("td:first-child") || {}).innerText || "",
        }));
      },
    });

    const appointments = results.flatMap((r) => r.result || []);
    sendToBackend({ type: "schedule_data", appointments });
  } catch (err) {
    console.error("[Videnti] extractScheduleFromActiveTab error:", err);
    sendToBackend({ type: "error", source: "extract_schedule", message: err.message });
  }
}

// ─── Extract Chart ────────────────────────────────────────────────────────────

async function extractChartFromActiveTab(mrn) {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tabs.length) return;

  try {
    // Send message to content script in ALL frames (eCW is frame-heavy).
    const responses = await Promise.all(
      (await chrome.webNavigation.getAllFrames({ tabId: tabs[0].id })).map(
        (frame) =>
          chrome.tabs
            .sendMessage(tabs[0].id, { action: "extract_chart" }, { frameId: frame.frameId })
            .catch(() => null)
      )
    );

    // Merge non-null responses — take the first frame that returned real data.
    const snapshot = responses
      .filter(Boolean)
      .filter((r) => r.ok && r.snapshot)
      .map((r) => r.snapshot)
      .find((s) => s.demographics && (s.demographics.mrn || s.demographics.name)) || null;

    sendToBackend({ type: "chart_data", mrn, snapshot });
  } catch (err) {
    console.error("[Videnti] extractChartFromActiveTab error:", err);
    sendToBackend({ type: "error", source: "extract_chart", message: err.message });
  }
}

// ─── Content-Script Messages ──────────────────────────────────────────────────

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  switch (message.action) {
    case "frame_ready":
      // Content script loaded — record the frame type in storage.
      chrome.storage.session.set({
        lastFrameType: message.frameType,
        lastFrameUrl: message.url,
      });
      break;

    case "get_status":
      sendResponse({ wsReady, reconnectAttempts });
      break;

    case "extract_chart_now":
      extractChartFromActiveTab(message.mrn || null)
        .then(() => sendResponse({ ok: true }))
        .catch((e) => sendResponse({ ok: false, error: e.message }));
      return true;  // Keep channel open for async response

    case "extract_schedule_now":
      extractScheduleFromActiveTab()
        .then(() => sendResponse({ ok: true }))
        .catch((e) => sendResponse({ ok: false, error: e.message }));
      return true;

    default:
      break;
  }
});

// ─── Popup Broadcast ─────────────────────────────────────────────────────────

function broadcastStatus(status) {
  chrome.storage.session.set({ wsStatus: status, wsUpdated: Date.now() });
  // Attempt to notify any open popup.
  broadcastToPopup({ type: "status_update", status });
}

function broadcastToPopup(data) {
  chrome.runtime.sendMessage(data).catch(() => {
    // Popup may be closed — ignore the error.
  });
}

// ─── Startup ─────────────────────────────────────────────────────────────────

connectWebSocket();

// Re-establish connection on Chrome startup / service-worker wakeup.
chrome.runtime.onStartup.addListener(connectWebSocket);
chrome.alarms.create("keepalive", { periodInMinutes: 0.5 });
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === "keepalive" && !wsReady) {
    connectWebSocket();
  }
});
