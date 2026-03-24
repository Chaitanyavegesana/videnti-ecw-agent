/**
 * Videnti eCW Bridge — Content Script
 *
 * Injected into every eClinicalWorks frame (including nested iframes).
 * Responsible for:
 *   1. Detecting which frame type is currently loaded (schedule, chart, orders).
 *   2. Extracting structured clinical data directly from the DOM.
 *   3. Forwarding extracted snapshots to the background service worker.
 *
 * HIPAA Note: Raw DOM text (potentially containing PHI) is extracted here but
 * is transmitted ONLY to the local background service worker, which in turn
 * sends it to the local ICS backend (ws://localhost:8001).  No data is
 * transmitted to any remote server at this stage.
 */

"use strict";

// ─── Frame-type Detection ─────────────────────────────────────────────────────

/**
 * Inspects the current document to determine what eCW page is loaded.
 * @returns {"schedule"|"chart"|"orders"|"login"|"unknown"}
 */
function detectFrameType() {
  const url = window.location.href;
  const title = document.title.toLowerCase();
  const body = document.body ? document.body.innerText.toLowerCase() : "";

  if (/login|signin|sign_in/i.test(url) || /sign in/i.test(title)) return "login";
  if (/schedule|appointment/i.test(url) || /appointment/i.test(title)) return "schedule";
  if (/orders?/i.test(url) || body.includes("new order")) return "orders";
  if (/chart|patient/i.test(url) || /patient chart/i.test(title)) return "chart";
  return "unknown";
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

/** Returns trimmed innerText of the first element matching *selector*, or null. */
function getText(selector, root = document) {
  const el = root.querySelector(selector);
  return el ? el.innerText.trim() : null;
}

/** Returns trimmed innerText of all elements matching *selector*. */
function getAllText(selector, root = document) {
  return Array.from(root.querySelectorAll(selector)).map((el) =>
    el.innerText.trim()
  );
}

// ─── Schedule Extraction ──────────────────────────────────────────────────────

/**
 * Parses the eCW appointment schedule screen.
 * eCW renders appointments as table rows with class "appt-row" (or similar).
 *
 * @returns {Array<{mrn: string, time: string, provider: string, visitType: string}>}
 */
function extractSchedule() {
  const appointments = [];

  // eCW schedule rows — adjust selectors for your eCW build/version.
  const rows = document.querySelectorAll(
    "tr.appt-row, tr[data-apptid], .appointmentRow, [class*='apptRow']"
  );

  rows.forEach((row) => {
    const mrn =
      row.getAttribute("data-mrn") ||
      getText("[class*='mrn'], [data-field='mrn']", row) ||
      "";
    const time =
      getText("[class*='appt-time'], [class*='apptTime'], td:first-child", row) ||
      "";
    const provider =
      getText("[class*='provider'], [data-field='provider']", row) || "";
    const visitType =
      getText("[class*='visit-type'], [data-field='visitType']", row) || "";

    if (mrn || time) {
      appointments.push({ mrn, time, provider, visitType });
    }
  });

  return appointments;
}

// ─── Chart Data Extraction ────────────────────────────────────────────────────

/**
 * Reads clinical data directly from an open eCW patient chart.
 * eCW uses a mix of named panels, iframes, and labelled table cells.
 *
 * Returns a raw snapshot dict.  This snapshot still contains PHI and must
 * be de-identified by the ICS backend before further processing.
 */
function extractChartData() {
  // ── Demographics ──────────────────────────────────────────────────────────
  const demographics = {
    name:
      getText("#patientName, [class*='patName'], [data-field='patientName']") ||
      getText(".patient-header-name") ||
      null,
    dob:
      getText("#patDOB, [data-field='dob'], [class*='dob']") ||
      null,
    mrn:
      getText("#patMRN, [data-field='mrn'], [class*='mrnNum']") ||
      null,
    sex:
      getText("#patSex, [data-field='sex']") ||
      null,
    age:
      getText("[class*='age'], [data-field='age']") ||
      null,
  };

  // ── Vitals ────────────────────────────────────────────────────────────────
  const vitalSelectors = {
    height: "[data-vital='height'], [class*='height-val'], #vitalHeight",
    weight: "[data-vital='weight'], [class*='weight-val'], #vitalWeight",
    bmi:    "[data-vital='bmi'],    [class*='bmi-val'],    #vitalBMI",
    bp:     "[data-vital='bp'],     [class*='bp-val'],     #vitalBP",
    hr:     "[data-vital='hr'],     [class*='hr-val'],     #vitalHR",
    temp:   "[data-vital='temp'],   [class*='temp-val'],   #vitalTemp",
  };
  const vitals = {};
  for (const [key, sel] of Object.entries(vitalSelectors)) {
    vitals[key] = getText(sel) || null;
  }

  // ── Problem List / PMH ────────────────────────────────────────────────────
  const pmh = getAllText(
    "[class*='problem-item'], [class*='pmhItem'], #problemList li, " +
    "[data-section='pmh'] li, .problem-list-row"
  );

  // ── Medications ───────────────────────────────────────────────────────────
  const medications = getAllText(
    "[class*='med-item'], [class*='medicationRow'], #medicationList li, " +
    "[data-section='medications'] li"
  );

  // ── Allergies ─────────────────────────────────────────────────────────────
  const allergies = getAllText(
    "[class*='allergy-item'], [class*='allergyRow'], #allergyList li, " +
    "[data-section='allergies'] li"
  );

  // ── Chief Complaint / HPI ─────────────────────────────────────────────────
  const chiefComplaint =
    getText("[data-section='cc'], #chiefComplaint, [class*='chiefComplaint']") ||
    null;
  const hpi =
    getText("[data-section='hpi'], #hpiText, [class*='hpiSection']") ||
    null;

  // ── Assessment / Plan ─────────────────────────────────────────────────────
  const assessment =
    getText("[data-section='assessment'], #assessmentText, [class*='assessment']") ||
    null;

  // ── Recent Labs ───────────────────────────────────────────────────────────
  const labRows = getAllText(
    "[class*='lab-row'], [class*='labResult'], #labResults tr, " +
    "[data-section='labs'] tr"
  );

  return {
    demographics,
    vitals,
    pmh,
    medications,
    allergies,
    chief_complaint: chiefComplaint,
    hpi,
    assessment,
    recent_labs: labRows,
    extraction_source: "chrome_extension_dom",
    page_url: window.location.href,
    extracted_at: new Date().toISOString(),
  };
}

// ─── Message Listener ─────────────────────────────────────────────────────────

/**
 * Listens for commands from the background service worker.
 *
 * Supported commands:
 *   - { action: "ping" }              → replies { ok: true }
 *   - { action: "detect_frame" }      → replies with frame type
 *   - { action: "extract_schedule" }  → extracts and replies with appointment list
 *   - { action: "extract_chart" }     → extracts and replies with chart snapshot
 */
chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  try {
    switch (message.action) {
      case "ping":
        sendResponse({ ok: true, frameType: detectFrameType() });
        break;

      case "detect_frame":
        sendResponse({ frameType: detectFrameType() });
        break;

      case "extract_schedule": {
        const appointments = extractSchedule();
        sendResponse({ ok: true, appointments });
        break;
      }

      case "extract_chart": {
        const snapshot = extractChartData();
        sendResponse({ ok: true, snapshot });
        break;
      }

      default:
        sendResponse({ ok: false, error: `Unknown action: ${message.action}` });
    }
  } catch (err) {
    sendResponse({ ok: false, error: err.message });
  }

  // Return true to keep the message channel open for async sendResponse.
  return true;
});

// ─── Auto-announce on load ────────────────────────────────────────────────────

// Tell the background script that this frame is ready.
chrome.runtime.sendMessage({
  action: "frame_ready",
  frameType: detectFrameType(),
  url: window.location.href,
});
