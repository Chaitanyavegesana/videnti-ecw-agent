# Architecture Diagrams

**Document:** System Architecture & Data Flow  
**Date:** March 6, 2026  
**Scope:** Complete system overview

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ┌─────────────────────┐         ┌──────────────────────────┐    │
│  │   Chrome Browser    │         │   Dashboard (React JSX)  │    │
│  │                     │         │                          │    │
│  │ • Manual Login      │         │ • Home Tab               │    │
│  │ • Cloudflare CAPTCHA│         │ • Audit Log Tab          │    │
│  │ • MFA               │         │ • Settings Tab           │    │
│  │ • Visual Anchors    │         │                          │    │
│  └──────────┬──────────┘         └────────┬─────────────────┘    │
│             │                             │                       │
│             │                             │                       │
└─────────────┼─────────────────────────────┼───────────────────────┘
              │ (Tab Detection)             │ (HTTP Polling)
              │                             │
┌─────────────┼─────────────────────────────┼───────────────────────┐
│             ▼                             ▼                        │
│  ┌──────────────────────────────────────────────┐               │
│  │                                              │               │
│  │       PYTHON APPLICATION LAYER               │               │
│  │                                              │               │
│  ├──────────────────────────────────────────────┤               │
│  │                                              │               │
│  │  ┌────────────────────────────────────────┐ │               │
│  │  │   Session Monitor Module               │ │               │
│  │  │                                        │ │               │
│  │  │  • SESSION_STATE (global)             │ │               │
│  │  │  • check_session_alive()              │ │               │
│  │  │  • get_session_status()               │ │               │
│  │  │  • mark_login_complete()              │ │               │
│  │  │  • reset_session()                    │ │               │
│  │  └────────────────────────────────────────┘ │               │
│  │                                              │               │
│  │  ┌────────────────────────────────────────┐ │               │
│  │  │   Chrome Helper Module                 │ │               │
│  │  │                                        │ │               │
│  │  │  • is_chrome_running()                │ │               │
│  │  │  • find_ecw_tab()                     │ │               │
│  │  │  • activate_ecw_tab()                 │ │               │
│  │  │  • is_on_ecw_page()                   │ │               │
│  │  │  • get_page_title()                   │ │               │
│  │  └────────────────────────────────────────┘ │               │
│  │                                              │               │
│  │  ┌────────────────────────────────────────┐ │               │
│  │  │   eCW Login Module                     │ │               │
│  │  │                                        │ │               │
│  │  │  • login_to_ecw()                     │ │               │
│  │  │    - Path 1: Already logged in        │ │               │
│  │  │    - Path 2: Prompt user              │ │               │
│  │  │    - Path 3: Verify login             │ │               │
│  │  │  • verify_login_success()             │ │               │
│  │  └────────────────────────────────────────┘ │               │
│  │                                              │               │
│  └──────────────────────────────────────────────┘               │
│                          ▲                                       │
└──────────────────────────┼───────────────────────────────────────┘
                           │ (State checking)
                           │
┌──────────────────────────┼───────────────────────────────────────┐
│                          │                                        │
│            MCP SERVER LAYER (FastAPI: Port 8000)                │
│                          │                                        │
│  ┌──────────────────────┴───────────────────────────────────┐   │
│  │                                                          │   │
│  │  FastAPI Application (uvicorn on 0.0.0.0:8000)          │   │
│  │                                                          │   │
│  │  ┌─────────────────────┐     ┌──────────────────────┐   │   │
│  │  │ Health Endpoints    │     │ Login Endpoints      │   │   │
│  │  │                     │     │                      │   │   │
│  │  │ GET /health    ─────┼────▶│ GET /login-status    │   │   │
│  │  │ Returns:           │     │ Returns SESSION_STATE│   │   │
│  │  │ • version          │     │                      │   │   │
│  │  │ • status           │     │ GET /session-check   │   │   │
│  │  │ • timestamp        │     │ Returns boolean      │   │   │
│  │  │                     │     │                      │   │   │
│  │  │                     │     │ POST /login-complete │   │   │
│  │  │                     │     │ Updates session      │   │   │
│  │  └─────────────────────┘     └──────────────────────┘   │   │
│  │                                                          │   │
│  │  ┌──────────────────────────────────────────────────┐   │   │
│  │  │ RPA Action Endpoints                             │   │   │
│  │  │                                                  │   │   │
│  │  │ POST /tools/approve_recommendation              │   │   │
│  │  │  • ensure_logged_in()                           │   │   │
│  │  │  • eCW RPA: Click Approve                       │   │   │
│  │  │  • Return: {"status": "SUCCESS"}                │   │   │
│  │  │                                                  │   │   │
│  │  │ POST /tools/dismiss_recommendation              │   │   │
│  │  │  • ensure_logged_in()                           │   │   │
│  │  │  • eCW RPA: Click Dismiss                       │   │   │
│  │  │  • Return: {"status": "SUCCESS"}                │   │   │
│  │  └──────────────────────────────────────────────────┘   │   │
│  │                                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌───────────────────────────────────────────────────────────────────┐
│                    eCW APPLICATION LAYER                          │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────────┐ │
│  │  eClinicalWorks Browser                                     │ │
│  │                                                             │ │
│  │  • Order workflow                                           │ │
│  │  • Approve button                                           │ │
│  │  • Dismiss button                                           │ │
│  │  • Patient info                                             │ │
│  │  • Clinical notes                                           │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow: User Login

```
START: System Cold Boot
   │
   ▼
┌──────────────────────────────┐
│ Dashboard loads              │
│ localhost:5173               │
└──────────┬───────────────────┘
           │
           ▼
┌──────────────────────────────┐
│ Fetch /login-status          │
│ (Check session)              │
└──────────┬───────────────────┘
           │
           ├─── SESSION.is_active = True
           │            │
           │            ▼
           │    Show green banner ✓
           │
           └─── SESSION.is_active = False
                        │
                        ▼
                ┌────────────────────────┐
                │ Show red banner        │
                │ "Please Login"         │
                └────────────┬───────────┘
                             │
                             ▼
                  ┌──────────────────────────┐
                  │ User opens Chrome        │
                  │ Manually                 │
                  └────────────┬─────────────┘
                               │
                               ▼
                  ┌──────────────────────────┐
                  │ User navigates to eCW    │
                  │ Sees Cloudflare CAPTCHA  │
                  └────────────┬─────────────┘
                               │
                               ▼
                  ┌──────────────────────────┐
                  │ User clicks CAPTCHA      │
                  │ Proves human             │
                  └────────────┬─────────────┘
                               │
                               ▼
                  ┌──────────────────────────┐
                  │ User enters credentials  │
                  │ eCW username/password    │
                  └────────────┬─────────────┘
                               │
                               ▼
                  ┌──────────────────────────┐
                  │ User completes MFA       │
                  │ (if required)            │
                  └────────────┬─────────────┘
                               │
                               ▼
                  ┌──────────────────────────┐
                  │ eCW loads successfully   │
                  │ Hub button visible       │
                  │ Orders list shown        │
                  └────────────┬─────────────┘
                               │
                               ▼
              ┌────────────────────────────────┐
              │ System detects login complete  │
              │                                │
              │ check_session_alive() checks:  │
              │  1. Chrome running? ✓          │
              │  2. eCW tab present? ✓         │
              │  3. Not on login page? ✓       │
              │  4. Hub button visible? ✓      │
              │  5. URL correct? ✓             │
              │  6. Returns: True              │
              └────────────┬───────────────────┘
                           │
                           ▼
              ┌────────────────────────────────┐
              │ Dashboard polls again          │
              │ GET /login-status              │
              └────────────┬───────────────────┘
                           │
                    ┌──────┴──────┐
                    ▼             ▼
              ┌──────────┐   ┌──────────────┐
              │ is_active│   │ Optional     │
              │ = True   │   │ user clicks  │
              │          │   │ "I've Logged │
              │ Green OK │   │ In" button   │
              └──────────┘   └──────┬───────┘
                                    │
                                    ▼
                             POST /login-complete
                             Updates session
                                    │
                                    ▼
              ┌────────────────────────────────┐
              │ Dashboard shows               │
              │ "Ready to Approve Orders"     │
              │ Green banner persists         │
              │                               │
              │ All action buttons enabled:   │
              │ • Approve Order               │
              │ • Dismiss Order               │
              │ • View Audit Log              │
              └──────────────┬─────────────────┘
                             │
                             ▼
                        END: Ready
```

---

## 🔄 Data Flow: Order Approval

```
User sees red order in eCW
         │
         ▼
User clicks order to select
         │
         ▼
User sees order details
loading in Dashboard sidebar
         │
         ▼
User clicks "Approve Order" button
         │
         ▼
Dashboard sends:
POST /tools/approve_recommendation
  body: {snapshot_id, user_id}
         │
         ▼
MCP Server receives request
         │
         ▼
ensure_logged_in() called:
  └─ check_session_alive()
     - If False: Show login prompt
     - If True: Continue
         │
         ▼
RPA Action: Approve
  └─ Switch to Chrome eCW tab
  └─ Locate Approve button
  └─ Click Approve
  └─ Wait for confirmation
  └─ Return timestamp
         │
         ▼
MCP returns:
{
  "status": "SUCCESS",
  "action": "approved",
  "timestamp": "2026-03-06T14:30:45",
  "snapshot_id": "123456"
}
         │
         ▼
Dashboard receives response
         │
         ▼
Log entry added to audit log:
{
  "timestamp": "2026-03-06T14:30:45",
  "action": "approved",
  "order_id": "123456",
  "user": "john_doe",
  "status": "SUCCESS"
}
         │
         ▼
Dashboard shows:
"✓ Order approved successfully"
         │
         ▼
Auto-hide success message (3s)
         │
         ▼
System ready for next action
```

---

## 🔄 Session Management Flow

```
                    SESSION_STATE
                         │
        ┌────────────────┼────────────────┐
        │                │                │
        ▼                ▼                ▼
    is_active      login_time      consecutive_failures
    (boolean)      (timestamp)      (counter)
       │                │                │
       │                │                │
   False on      First login           Reset to 0
   fresh boot    timestamp             on success
       │         stored here
       │
   Updated by:
   1. mark_login_complete()
      └─ Set to True
   2. check_session_alive()
      └─ Verify state
   3. reset_session()
      └─ Set to False
       │
       ▼
   Every 10 seconds (client-side poll):
   GET /login-status
      └─ Return current SESSION_STATE
         └─ Dashboard shows green/red
            banner based on is_active
       │
       ▼
   Session validation checks:
   • Chrome process running?
   • eCW tab exists?
   • On correct page?
   • Hub button visible?
   • URL matches eCW?
       │
       ├─ All 6 checks pass
       │      └─ is_active = True ✓
       │
       └─ Any check fails
              └─ is_active = False ✗
                 └─ Dashboard prompts
                    re-login
```

---

## 🔐 Security Architecture

```
┌──────────────────────────────────────┐
│        Security Perimeter            │
├──────────────────────────────────────┤
│                                      │
│  Layer 1: Authentication             │
│  ┌──────────────────────────────────┐│
│  │ Manual user login in Chrome       ││
│  │ • Cloudflare CAPTCHA (human)      ││
│  │ • eCW credentials (user-entered)  ││
│  │ • MFA (if enabled)                ││
│  │                                   ││
│  │ NO automatic login attempts       ││
│  └──────────────────────────────────┘│
│                                      │
│  Layer 2: Credential Handling        │
│  ┌──────────────────────────────────┐│
│  │ ZERO credential storage           ││
│  │ ZERO credential transmission      ││
│  │ ZERO credential logging           ││
│  │                                   ││
│  │ Only session state tracked:       ││
│  │ • is_active (boolean)             ││
│  │ • login_time (timestamp)          ││
│  └──────────────────────────────────┘│
│                                      │
│  Layer 3: Session Security           │
│  ┌──────────────────────────────────┐│
│  │ Session timeout: 4-8+ hours       ││
│  │ Inactivity timeout: 2 hours       ││
│  │ Tab verification: Every action    ││
│  │ HTTPS ready: Yes                  ││
│  │ CORS enabled: Selective           ││
│  └──────────────────────────────────┘│
│                                      │
│  Layer 4: Cloudflare Safety          │
│  ┌──────────────────────────────────┐│
│  │ ✓ Never launch Chrome             ││
│  │ ✓ Never solve CAPTCHA             ││
│  │ ✓ Never program credentials       ││
│  │ ✓ Never bypass security           ││
│  │ ✓ Always visual verification      ││
│  └──────────────────────────────────┘│
│                                      │
└──────────────────────────────────────┘
```

---

## 📊 Component Interaction Matrix

```
                      Session    Chrome    eCW       MCP
                      Monitor    Helper    Login     Server
                      ┌─────────┬────────┬─────────┬──────┐
Session Monitor       │  Self   │ Calls  │ Called  │●     │
                      ├─────────┼────────┼─────────┼──────┤
Chrome Helper         │         │ Self   │ Calls   │●     │
                      ├─────────┼────────┼─────────┼──────┤
eCW Login            │ Calls   │ Calls  │ Self    │●     │
                      ├─────────┼────────┼─────────┼──────┤
MCP Server           │ Queries │ -      │ Calls   │ Self │
                      └─────────┴────────┴─────────┴──────┘

Legend: ● = Interacts, Calls = Direct function call
```

---

## 🎯 Deployment Architecture

```
┌────────────────────────────────────────────┐
│   Development/Production Machine (macOS)   │
│                                            │
│  ┌──────────────────────────────────────┐ │
│  │  Terminal 1: MCP Server              │ │
│  │  python3 mcp_servers/ecw_bridge/...  │ │
│  │  Listening on :8000                  │ │
│  └──────────────────────────────────────┘ │
│                                            │
│  ┌──────────────────────────────────────┐ │
│  │  Terminal 2: Dashboard               │ │
│  │  cd dashboard && npm run dev          │ │
│  │  Listening on :5173                  │ │
│  └──────────────────────────────────────┘ │
│                                            │
│  ┌──────────────────────────────────────┐ │
│  │  Chrome Browser (Manual)             │ │
│  │  User login + RPA operations         │ │
│  └──────────────────────────────────────┘ │
│                                            │
└────────────────────────────────────────────┘
```

---

**Note:** This architecture document complements the technical implementation.  
For more details, see [CLOUDFLARE_LOGIN_FIX_PLAN.md](CLOUDFLARE_LOGIN_FIX_PLAN.md) and [SYSTEM_STATUS_REPORT.md](SYSTEM_STATUS_REPORT.md).
