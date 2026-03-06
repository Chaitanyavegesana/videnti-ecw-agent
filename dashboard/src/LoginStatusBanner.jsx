/**
 * LoginStatusBanner Component
 * Real-time session status display with user confirmation workflow
 * Polls /login-status endpoint every 10 seconds
 */

import React, { useState, useEffect } from 'react';
import './LoginStatusBanner.css';

const LoginStatusBanner = () => {
  const [sessionStatus, setSessionStatus] = useState(null);
  const [showBanner, setShowBanner] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Poll for login status every 10 seconds
  useEffect(() => {
    const checkLoginStatus = async () => {
      try {
        const response = await fetch('http://localhost:8001/login-status', {
          headers: { 'Origin': 'http://localhost:5173' }
        });
        const data = await response.json();
        setSessionStatus(data);

        // Show banner if not logged in
        if (!data.is_active) {
          setShowBanner(true);
        }
      } catch (error) {
        console.error('Error checking login status:', error);
      }
    };

    // Check on mount
    checkLoginStatus();

    // Poll every 10 seconds
    const interval = setInterval(checkLoginStatus, 10000);
    return () => clearInterval(interval);
  }, []);

  const handleLoginConfirm = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:8001/login-complete', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      if (response.ok) {
        const data = await response.json();
        setSessionStatus(data);

        if (data.is_active) {
          // Show success message
          setShowBanner(true);
          setTimeout(() => setShowBanner(false), 3000);
        }
      }
    } catch (error) {
      console.error('Error confirming login:', error);
    } finally {
      setIsLoading(false);
    }
  };

  if (!showBanner || !sessionStatus) {
    return null;
  }

  const isActive = sessionStatus.is_active;

  return (
    <div
      className={`login-status-banner ${isActive ? 'banner-success' : 'banner-warning'}`}
    >
      <div className="banner-content">
        {isActive ? (
          <>
            <strong>✓ Session Active</strong>
            <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.85rem' }}>
              You are logged into eClinicalWorks
            </p>
          </>
        ) : (
          <>
            <strong>⚠ Login Required</strong>
            <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.85rem' }}>
              Please complete Cloudflare verification in Chrome
            </p>
          </>
        )}
      </div>

      {!isActive && (
        <button
          className="banner-button"
          onClick={handleLoginConfirm}
          disabled={isLoading}
        >
          {isLoading ? 'Checking...' : "I've Logged In"}
        </button>
      )}
    </div>
  );
};

export default LoginStatusBanner;

