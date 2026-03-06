# Quick Start Guide

**Start Time:** 2 minutes  
**Full Setup:** 10 minutes  
**System Ready:** YES ✅

---

## 1️⃣ Verify Python & Dependencies (30 seconds)

```bash
# Check Python version
python3 --version
# Expected: Python 3.8+

# Check dependencies installed
pip list | grep pytest
pip list | grep playwright
# Expected: Both present
```

**If missing:**
```bash
pip install pytest pytest-asyncio playwright
```

---

## 2️⃣ Start Dashboard (1 minute)

```bash
# Navigate to dashboard
cd dashboard

# Install node dependencies (first time only)
npm install

# Start Vite dev server
npm run dev

# Expected output:
# ➜ Local: http://localhost:5173/
```

**Dashboard loads at:** `http://localhost:5173`

---

## 3️⃣ Start MCP Server (1 minute)

**In a new terminal:**

```bash
# From project root
cd /Users/chaitanya/Desktop/videnti-ecw-agent

# Run MCP server
python3 mcp_servers/ecw_bridge/server.py

# Expected output# Expected output# Expected output# Expected output# Expected output# Expected outpuca# Expected outpu

## ## ## ## ## ## ## ## ## ##n ## ## # - 2 minutes)

```bash```bash```bash```bually
# Comman# Comman# Comman# Comman# Comman# Comman# Comman#o eCW## URL: # Comman# Comman# orks.# Comman# C specific instance

# Complete l# Complete l# Complete l Click # Complete l# CompleAPT# Complete l# Complete l#ti# Complete l# Complete if required)
# 4. Wait for dashboard to load
```

**Dashboard will automatically detect login.**

---

## 5️⃣ Check Dashboard Status (10 seconds)

**In browser:**
```
Go to: http://localhost:5173
```

**Expected:**
- ✅ Green banner: "Logged In - You're ready to approve orders"
- ✅ Audit Log tab working
- ✅ Settings tab working

---

## ✅ System Ready!

All systems operational:
- ✅ Dashboard running on port 5173
- ✅ MCP Server running on port 8000
- ✅ Session verified
- ✅ Ready to use

---

## 🎯 Next Steps

### Approve an Order
1. In eCW: Click an ord1. In eCW: Click an ord1. In eCW: Click an ord1. In eCW: Click an ord1. marked complete
4. Dashboard: Shows success notif4. Dashboard: Shows success notif4. Dashboard: Shoudit Log" tab
2. See all approved/2. See all approved/2. See all approved/2. See all approved/2. See all approved/2. See all approved/2. See all approved/ser 2. See all approved/2. See all approved/2. See all approved/2. See all approved/2. See all approved/2. See all approved/2. See ning
lsof -i :8000

# Kill and restart if needed
# In server terminal: Ctrl+C
# Then: p# hon# Then: p# hon# Then: p# hon# Then: p# hon# Dash# Then: p# honot# og# Then: p# hon# Then: p# he m# ual login in Chrome:
# 1. Chrome should already have eCW open
# 2. If not: navigate to eCW
# 3. Complete login flow
# 4. Wait 5 seconds
# 5. Re# 5. Re# 5. Re# (Cmd+R# 5. Re# 5. Re# 5. Re# ts# 5. Re# 5. Re# 5. Re# (Cmd+R# 5. R
lsof -i :5173    # Dashboard port
lsof lsof lsof lsof lP Server port

# Kill if needed
kill -9 <PID>
```

------------------- Architecture

```
┌──────────────────────────────�┌──────────────────────────────�A)┌──────────────────────────────�┌──────────────────────────────�A)┌───────────────────────────┌──┐
�����������(Python)           │
│ - Detects a│ - Detects a│ - Detects a│ - Detects a│ - Detects a│ - Detects a│ - Detects a│ - Detects a│ - Detects a│ - Det─�│ - Detects a│ - Detects a│ - �──────┘
               │
      ┌────────┴�      ┌────────┴�      ┌────────┴�      ┌─└�      ┌───────��      ┌───────�─�      ┌� MCP S      ┌�  │  D      ┌──────�        │  │  :5173           │
└──────────────┘  └──────────────────┘
      │                    │
      └────────┬───────────┘
               ▼
         ┌──────────────┐
         │   eCW RPA    │
         │ Approve/Deny │
         └──────────────┘
```

---

## 🎮 Full Workflow

### 1. S### 1. S### 1. S### 1. S### 1. S### 1. S##l 1### 1. S### 1. S### 1. S### 1. S### 1. S### 1. S##l 1### 1. S### 1. S### 1. S### 1. S### 1. S### 1. S##l 1### 1. S### 1. S### 1. S### 1. S### 1. S### 1. S##l 1### 1. S### 1. S### 1. S### 1. S### 1. S### 1. rv### 1. S### 1. Sing### 1. S### 1. S### 1. S### 1. S### 1. S### 1. S##l 1### 1. S### 1. S### 1. S### 1. S### 1. S### 1. S##l 1### 1. S### 1. S### 1. S### 1. S### 1. S### 1. S##l 1### 1. S### 1. S### 1. S### 1. S### 1. S### 1. S##l 1### 1. S### 1. S### 1. S### 1. S### 1. S### 1. rv### 1. S### 1. Sing### 1. S### 1. S#bs

### Home Tab
- Current login status
- Quick action buttons
- Real-time order count

### Audit Log Tab
- All c- All c- All c- All c- All c- A U- All c- All c- All c- All c- All c- A U- All c- All c- All c- All c- Anc- All c- All c- Al - All c- All c- All c- All c- All c- A U- All c- All c-
---

## 🚀 Common Commands

`````````````````````````` is ru`````````````````````````` is ru````````````````````````n status
curl http://localhost:8000/login-status

# Test MCP endpoints
curl http://localhost:8000/tools/list

# View dashboard logs
tail -f logs/dashboard.log

# View server logs
tail -f logs/server.log
```

---

## ⏱️ Session Timeout

- **Session Duration:** 4-8+ hours
- **Inactivity Timeout:** Configurable (default: 2 hours)
- **Auto-Logout:** Yes (after timeout)
- **Re-Login:** Manual required

---

## 📞 Quick Support

| Issue | Solution |
|-------|----------|
| Dashboard blank | Refresh (Cmd+R) |
| Can't login | Check Chrome has eCW open |
| MCP error | Restart: Ctrl+C, then run again |
| Orders not updating | Verify session status in Settings |
| Cloudfla| Cloudfla| Cloudfla| PTC| Cloudfla| Cn Chr| Cloudfla| Cloudfla| Cloudfla| PTC| Cloudfla| Cn Chr| Cloudfla| Cloudfla| Cloudfla| PTC| Cloudfla| Cn Chr| Cloudfla| Cloudfla| Cloudfla| PTC| Cloudfla| Cn Chr| Cloudfla| Cloudfla| Cloub

### P### P### P### P### P##board in separate window
- Use full-screen for better UX
- Minimize distractions during approval

####################################### (10###################dit log to track completions
- Set auto-approval rules in Setti- Set auto-approval rrning P- Set auto-appt her- Set auto-approval ru2. **See det- Set auto-approval ruDE.md- Set auto-approval rules in Sersta- Set auto-approval rules in Setti- Set auto-approv**Fix i- Set auto-approval rules in Setti-.md]- Set auto-approval rules in S

---

#####################You################:
- �- �- �- �- orders in eCW
- ✅ Dismiss non-matching orders
- ✅ Track all actions in audit log
- ✅ Manage user settings

**Let's go! 🚀**

