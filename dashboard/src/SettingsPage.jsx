import React, { useState } from 'react';

export default function SettingsPage({ onSave }) {
    const [credentials, setCredentials] = useState({
        ecw_url: '',
        ecw_username: '',
        ecw_password: '',
        ecw_clinic_id: '',
        ecw_mfa: 'manual',
        ollama_base_url: 'http://localhost:11434',
        mrn_salt: '',
    });
    const [saved, setSaved] = useState(false);

    const handleChange = (e) => {
        setCredentials({ ...credentials, [e.target.name]: e.target.value });
    };

    const handleSave = async () => {
        // In production this would POST to the local ecw-bridge to write .env.
        // For now simulate a local save.
        console.log('Credentials saved locally (NOT sent to cloud):', credentials);
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
        if (onSave) onSave(credentials);
    };

    return (
        <div>
            <div className="header">
                <div className="header-title">
                    <h1>System Configuration</h1>
                    <p>eCW Portal credentials &amp; Ollama settings — stored locally only</p>
                </div>
            </div>

            <div className="content-card" style={{ maxWidth: 720 }}>
                <div className="card-header">
                    <div className="card-title"><h3>eClinicalWorks Portal Access</h3></div>
                    <span className="badge badge-success" style={{ fontSize: '0.75rem' }}>🔒 Local Only</span>
                </div>

                <div className="form-grid">
                    <div className="form-group">
                        <label className="form-label">eCW Portal URL</label>
                        <input
                            id="ecw_url"
                            name="ecw_url"
                            type="url"
                            className="form-input"
                            placeholder="https://provider.eclinicalworks.com/..."
                            value={credentials.ecw_url}
                            onChange={handleChange}
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Clinic ID</label>
                        <input
                            id="ecw_clinic_id"
                            name="ecw_clinic_id"
                            type="text"
                            className="form-input"
                            placeholder="Your unique eCW clinic identifier"
                            value={credentials.ecw_clinic_id}
                            onChange={handleChange}
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Username</label>
                        <input
                            id="ecw_username"
                            name="ecw_username"
                            type="text"
                            className="form-input"
                            placeholder="RPA service account username"
                            value={credentials.ecw_username}
                            onChange={handleChange}
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">Password</label>
                        <input
                            id="ecw_password"
                            name="ecw_password"
                            type="password"
                            className="form-input"
                            placeholder="••••••••••••"
                            value={credentials.ecw_password}
                            onChange={handleChange}
                        />
                    </div>

                    <div className="form-group">
                        <label className="form-label">MFA Method</label>
                        <select
                            id="ecw_mfa"
                            name="ecw_mfa"
                            className="form-input"
                            value={credentials.ecw_mfa}
                            onChange={handleChange}
                        >
                            <option value="manual">Manual (Agent pauses for human MFA)</option>
                            <option value="totp">TOTP Authenticator</option>
                            <option value="sms">SMS (Not Recommended)</option>
                            <option value="none">None</option>
                        </select>
                    </div>

                    <div className="form-group">
                        <label className="form-label">MRN Salt (HIPAA Anonymization)</label>
                        <input
                            id="mrn_salt"
                            name="mrn_salt"
                            type="password"
                            className="form-input"
                            placeholder="Random 32+ character secret"
                            value={credentials.mrn_salt}
                            onChange={handleChange}
                        />
                    </div>
                </div>

                {/* Divider */}
                <div style={{ borderTop: '1px solid var(--border-color)', margin: '2rem 0' }} />

                <div className="card-header">
                    <div className="card-title"><h3>Ollama Local Inference</h3></div>
                </div>

                <div className="form-grid">
                    <div className="form-group">
                        <label className="form-label">Ollama Base URL</label>
                        <input
                            id="ollama_base_url"
                            name="ollama_base_url"
                            type="url"
                            className="form-input"
                            value={credentials.ollama_base_url}
                            onChange={handleChange}
                        />
                    </div>
                </div>

                <div style={{ marginTop: '2rem', display: 'flex', gap: '1rem', alignItems: 'center' }}>
                    <button className="btn btn-primary" onClick={handleSave}>
                        Save to local .env
                    </button>
                    {saved && (
                        <span style={{ color: 'var(--success)', fontWeight: 600, animation: 'fadeIn 0.3s ease' }}>
                            ✓ Saved locally
                        </span>
                    )}
                </div>

                <div style={{ marginTop: '1.5rem', padding: '1rem', background: 'rgba(245, 158, 11, 0.05)', border: '1px solid rgba(245, 158, 11, 0.2)', borderRadius: '12px' }}>
                    <p style={{ color: 'var(--warning)', fontSize: '0.85rem' }}>
                        ⚠️ These credentials are written to your local <code>.env</code> file and are NEVER transmitted to any cloud service. Do not share or commit this file.
                    </p>
                </div>
            </div>
        </div>
    );
}
