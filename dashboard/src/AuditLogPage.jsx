import React, { useState } from 'react';

const MOCK_AUDIT = [
    { ts: '2026-02-28 07:31:04', action: 'summarize_phi', snapshot_id: 'v-9a1b-...', status: 'SUCCESS', phi_stripped: true },
    { ts: '2026-02-28 07:31:07', action: 'validate_eligibility', snapshot_id: 'v-9a1b-...', status: 'SUCCESS', phi_stripped: true },
    { ts: '2026-02-28 07:32:11', action: 'open_chart', snapshot_id: 'v-3c2d-...', status: 'SUCCESS', phi_stripped: true },
    { ts: '2026-02-28 07:32:18', action: 'pend_order', snapshot_id: 'v-3c2d-...', status: 'PENDING_APPROVAL', phi_stripped: true },
    { ts: '2026-02-28 08:00:00', action: 'scan_repo', snapshot_id: 'N/A', status: 'SUCCESS', phi_stripped: true },
];

export default function AuditLogPage() {
    const [filter, setFilter] = useState('ALL');

    const filtered = filter === 'ALL' ? MOCK_AUDIT : MOCK_AUDIT.filter(l => l.status === filter);

    return (
        <div>
            <div className="header">
                <div className="header-title">
                    <h1>HIPAA Audit Log</h1>
                    <p>Read-only, local audit trail — zero PHI stored</p>
                </div>
                <div style={{ display: 'flex', gap: '0.5rem' }}>
                    {['ALL', 'SUCCESS', 'PENDING_APPROVAL'].map(f => (
                        <button
                            key={f}
                            onClick={() => setFilter(f)}
                            className={`btn ${filter === f ? 'btn-primary' : 'btn-ghost'}`}
                            style={{ padding: '0.5rem 1rem', fontSize: '0.8rem' }}
                        >
                            {f}
                        </button>
                    ))}
                </div>
            </div>

            <div className="content-card">
                <table className="videnti-table">
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>MCP Action</th>
                            <th>Snapshot ID</th>
                            <th>PHI Stripped</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filtered.map((log, idx) => (
                            <tr key={idx}>
                                <td><code style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>{log.ts}</code></td>
                                <td><strong>{log.action}</strong></td>
                                <td><code style={{ fontSize: '0.8rem' }}>{log.snapshot_id}</code></td>
                                <td>
                                    <span style={{ color: log.phi_stripped ? 'var(--success)' : 'var(--danger)' }}>
                                        {log.phi_stripped ? '✓ Yes' : '✗ No'}
                                    </span>
                                </td>
                                <td>
                                    <span className={`badge ${log.status === 'SUCCESS' ? 'badge-success' : 'badge-pending'}`}>
                                        {log.status}
                                    </span>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
