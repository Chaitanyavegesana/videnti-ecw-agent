# Videnti Clinical AI Project Context

The **videnti-ecw-agent** is a local-first clinical automation suite designed to interface with the **eClinicalWorks (eCW)** EMR system. Its primary focus is on **AI-driven patient chart analysis** and **eligibility validation** while strictly maintaining patient privacy through local processing.

---

## 1. Core Objectives
*   **Daily Clinical Scans**: Automatically scan the doctor's daily schedule via RPA.
*   **Local PHI Stripping**: Use local LLMs (Ollama) to anonymize patient charts before any high-level reasoning is performed.
*   **Coding & Eligibility Validation**: Cross-reference chart data against CMS, FDA, and LCD guidelines (CPT/ICD codes).
*   **Local Automation (RPA)**: Control the eCW UI to pull charts and pend diagnostic orders.

---

## 2. Project Structure & Architecture
*   **`/main.py` (The Orchestrator)**: Uses `APScheduler` to run daily clinical scan pipelines (7:30 AM) and weekly legislative research updates (Mon 8:00 AM).
*   **`/mcp_servers/` (The Engines)**:
    *   `ecw_bridge`: Uses `PyAutoGUI` to navigate eCW, extract data, and perform UI actions.
    *   `ollama_server`: Provides local LLM endpoints for medical summarization and PHI protection.
    *   `search_mcp`: Monitors federal/state medical repositories for coding rule changes.
*   **`/dashboard/`**: Local interface for monitoring the agent's actions and recommendations.
*   **`/guidelines/`**: Storage for CMS/LCD rules and historical coding snapshots.
*   **`/Docs/`**: Contains PDF/Markdown documentation for architecture, skills, and instructions.

---

## 3. Current Development State
*   **GitHub**: Repository initialized and synced at `https://github.com/Chaitanyavegesana/videnti-ecw-agent`.
*   **Infrastructure**: Initial `main.py` pipeline is in place with mocking for testing local MCP connections.

---

## 4. Key Tech Stack
*   **Language**: Python 3.13 (AsyncIO)
*   **Privacy**: Ollama (MedGemma / DeepSeek-R1)
*   **EMR Bridge**: PyAutoGUI (RPA)
*   **Orchestration**: APScheduler, HTTPX
*   **Interoperability**: Model Context Protocol (MCP)
