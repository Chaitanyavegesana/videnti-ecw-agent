import React, { useState } from 'react';
import SettingsPage from './SettingsPage';
import AuditLogPage from './AuditLogPage';

// ─── Mock Data ──────────────────────────────────────────────────────────────

const MOCK_STATS = [
  { label: 'Total Scans', value: '1,284', trend: '+12%', type: 'up' },
  { label: 'Pending Approvals', value: '18', trend: '-2', type: 'down' },
  { label: 'Qualified Tests', value: '412', trend: '+5%', type: 'up' },
  { label: 'Revenue Identified', value: '$104.2k', trend: '+$8.4k', type: 'up' },
];

const MOCK_QUEUE = [
  { id: 'v-9a1b', mrn: 'MRN-7721', test: 'Home Sleep Test', confidence: '94%', status: 'Pending', date: '2026-02-28' },
  { id: 'v-3c2d', mrn: 'MRN-8842', test: 'EEG (95816)', confidence: '88%', status: 'Qualified', date: '2026-02-27' },
  { id: 'v-5e6f', mrn: 'MRN-1102', test: 'Allergy Panel', confidence: '91%', status: 'Pending', date: '2026-02-28' },
];

// ─── SVG Icons ──────────────────────────────────────────────────────────────

const IconDashboard = () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="3" y="3" width="7" height="7"></rect><rect x="14" y="3" width="7" height="7"></rect><rect x="14" y="14" width="7" height="7"></rect><rect x="3" y="14" width="7" height="7"></rect></svg>;
const IconActivity = () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"></path></svg>;
const IconShield = () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path></svg>;
const IconSettings = () => <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>;

// ─── Components ─────────────────────────────────────────────────────────────

function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [pipelineState, setPipelineState] = useState('STOPPED'); // STOPPED, RUNNING, PAUSED
  const [queue, setQueue] = useState(MOCK_QUEUE);
  const [actionLoading, setActionLoading] = useState({});

  // Handle Approve action
  const handleApprove = async (itemId) => {
    setActionLoading({ ...actionLoading, [itemId]: true });
    try {
      const response = await fetch('http://localhost:8001/tools/approve_recommendation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ snapshot_id: itemId })
      });
      
      if (response.ok) {
        // Remove from queue and show success
        setQueue(queue.filter(item => item.id !== itemId));
        alert(`✓ Approved ${itemId} - Order will be pending in eCW`);
      } else {
        alert(`✗ Failed to approve: ${response.statusText}`);
      }
    } catch (error) {
      alert(`✗ Error: ${error.message}`);
    } finally {
      setActionLoading({ ...actionLoading, [itemId]: false });
    }
  };

  // Handle Dismiss action
  const handleDismiss = async (itemId) => {
    setActionLoading({ ...actionLoading, [itemId]: true });
    try {
      const response = await fetch('http://localhost:8001/tools/dismiss_recommendation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ snapshot_id: itemId })
      });
      
      if (response.ok) {
        // Remove from queue and log dismissal
        setQueue(queue.filter(item => item.id !== itemId));
        alert(`✓ Dismissed ${itemId}`);
      } else {
        alert(`✗ Failed to dismiss: ${response.statusText}`);
      }
    } catch (error) {
      alert(`✗ Error: ${error.message}`);
    } finally {
      setActionLoading({ ...actionLoading, [itemId]: false });
    }
  };

  return (
    <div className="dashboard-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="brand">
          <IconShield />
          <span>Videnti AI</span>
        </div>
        <nav>
          <ul className="nav-links">
            <li>
              <a
                href="#"
                className={`nav-item ${activeTab === 'dashboard' ? 'active' : ''}`}
                onClick={() => setActiveTab('dashboard')}
              >
                <IconDashboard /> Dashboard
              </a>
            </li>
            <li>
              <a
                href="#"
                className={`nav-item ${activeTab === 'activity' ? 'active' : ''}`}
                onClick={() => setActiveTab('activity')}
              >
                <IconActivity /> Audit Log
              </a>
            </li>
            <li>
              <a
                href="#"
                className={`nav-item ${activeTab === 'settings' ? 'active' : ''}`}
                onClick={() => setActiveTab('settings')}
              >
                <IconSettings /> Settings
              </a>
            </li>
          </ul>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        <header className="header">
          <div className="header-title">
            <h1>Clinical Intelligence Dashboard</h1>
            <p>Monitoring local eCW bridge & PHI anonymization pipeline</p>
          </div>
          <div className="pipeline-controls">
            <button
              className={`btn ${pipelineState === 'RUNNING' ? 'btn-ghost' : 'btn-primary'}`}
              onClick={() => setPipelineState(pipelineState === 'RUNNING' ? 'STOPPED' : 'RUNNING')}
            >
              {pipelineState === 'RUNNING' ? 'Stop Pipeline' : 'Start Daily Scan'}
            </button>
          </div>
        </header>

        {activeTab === 'activity' && <AuditLogPage />}
        {activeTab === 'settings' && <SettingsPage />}

        {/* Stats Grid — only shown on dashboard tab */}
        {activeTab === 'dashboard' && <section className="stats-grid">
          {MOCK_STATS.map((stat, idx) => (
            <div key={idx} className="stat-card">
              <div className="stat-label">{stat.label}</div>
              <div className="stat-value">{stat.value}</div>
              <div className={`stat-trend ${stat.type === 'up' ? 'trend-up' : 'trend-down'}`}>
                {stat.trend} from last month
              </div>
            </div>
          ))}
        </section>}

        {/* Approval Queue + System Health — dashboard only */}
        {activeTab === 'dashboard' && <section className="content-card shadow-lg">
          <div className="card-header">
            <div className="card-title">
              <h3>Qualified Test Recommendations</h3>
            </div>
            <button className="btn btn-ghost">View All History</button>
          </div>
          <table className="videnti-table">
            <thead>
              <tr>
                <th>Snapshot ID</th>
                <th>Patient MRN</th>
                <th>Recommended Test</th>
                <th>AI Confidence</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {queue.length > 0 ? queue.map((item, idx) => (
                <tr key={idx}>
                  <td><code>{item.id}</code></td>
                  <td>{item.mrn}</td>
                  <td>{item.test}</td>
                  <td>
                    <span style={{ color: parseInt(item.confidence) > 90 ? 'var(--success)' : 'var(--accent-secondary)' }}>
                      {item.confidence}
                    </span>
                  </td>
                  <td>
                    <span className={`badge ${item.status === 'Pending' ? 'badge-pending' : 'badge-success'}`}>
                      {item.status}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      <button 
                        className="btn btn-primary" 
                        style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}
                        onClick={() => handleApprove(item.id)}
                        disabled={actionLoading[item.id]}
                      >
                        {actionLoading[item.id] ? '...' : 'Approve'}
                      </button>
                      <button 
                        className="btn btn-ghost" 
                        style={{ padding: '0.4rem 0.8rem', fontSize: '0.8rem' }}
                        onClick={() => handleDismiss(item.id)}
                        disabled={actionLoading[item.id]}
                      >
                        {actionLoading[item.id] ? '...' : 'Dismiss'}
                      </button>
                    </div>
                  </td>
                </tr>
              )) : (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', padding: '2rem', color: 'var(--text-secondary)' }}>
                    No pending recommendations
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </section>}

        {activeTab === 'dashboard' && /* System Health */(
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
            <div className="content-card">
              <div className="card-header">
                <div className="card-title"><h3>MCP Status</h3></div>
              </div>
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <li style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span className="text-secondary">Ollama Server (:8000)</span>
                  <span className="badge badge-success">Online</span>
                </li>
                <li style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span className="text-secondary">eCW Bridge (:8001)</span>
                  <span className="badge badge-success">Connected</span>
                </li>
                <li style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span className="text-secondary">Search MCP (:8002)</span>
                  <span className="badge badge-success">Online</span>
                </li>
              </ul>
            </div>
            <div className="content-card">
              <div className="card-header">
                <div className="card-title"><h3>HIPAA Guardrails</h3></div>
              </div>
              <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                <li style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span className="text-secondary">Data Residency</span>
                  <span style={{ color: 'var(--success)' }}>Local Only</span>
                </li>
                <li style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span className="text-secondary">PHI Anonymization</span>
                  <span style={{ color: 'var(--success)' }}>Active</span>
                </li>
                <li style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span className="text-secondary">Audit Encryption</span>
                  <span style={{ color: 'var(--accent-secondary)' }}>AES-256</span>
                </li>
              </ul>
            </div>
          </div>)}
      </main>
    </div>
  );
}

export default App;
