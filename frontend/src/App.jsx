import { useState, useEffect, useRef } from 'react';
import './App.css';

const API_BASE = 'http://localhost:8000/api';

function ScoreBadge({ score }) {
  const color = score >= 70 ? 'score-high' : score >= 40 ? 'score-medium' : 'score-low';
  return (
    <div className={`score-badge ${color}`}>
      <span className="score-number">{score}</span>
      <span className="score-bar-track">
        <span className="score-bar-fill" style={{ width: `${score}%` }} />
      </span>
    </div>
  );
}

function ActionBadge({ action }) {
  const map = {
    ONE_TIME_RECOVERY: 'action-recovery',
    MONITOR: 'action-monitor',
    ESCALATE: 'action-escalate',
    STOP: 'action-stop',
    PAYMENT_METHOD_RECOVERY: 'action-pmr',
  };
  return <span className={`action-badge ${map[action] || 'action-monitor'}`}>{action?.replace(/_/g, ' ')}</span>;
}

function CopyButton({ text }) {
  const [copied, setCopied] = useState(false);
  const handleCopy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };
  return (
    <button className="copy-btn" onClick={handleCopy} title="Copy message">
      {copied ? 'Copied!' : 'Copy AI Draft'}
    </button>
  );
}

function AIInsights({ cases }) {
  if (!cases || cases.length === 0) return null;
  
  // Calculate top failure reason
  const reasons = {};
  cases.forEach(c => {
    const reason = c.diagnosis?.split(':')[0]?.trim() || 'unknown';
    reasons[reason] = (reasons[reason] || 0) + 1;
  });
  const topReason = Object.entries(reasons).sort((a, b) => b[1] - a[1])[0];
  const percentage = topReason ? Math.round((topReason[1] / cases.length) * 100) : 0;
  
  return (
    <div className="insights-panel">
      <div className="insights-header">
        <span className="insights-icon">✦</span>
        <h3>Vasooli Intelligence Insights</h3>
      </div>
      <div className="insights-content">
        <div className="insight-item">
          <strong>Key Finding:</strong> {percentage}% of recent payment failures are due to <span className="highlight-tag">{topReason ? topReason[0] : 'Various Reasons'}</span>.
        </div>
        <div className="insight-item">
          <strong>Auto-Action Taken:</strong> The AI Policy Engine is prioritizing <em>Smart Retries</em> and generating personalized payment links for high-tenure customers to prevent involuntary churn.
        </div>
      </div>
    </div>
  );
}

function App() {
  const [stats, setStats] = useState(null);
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [simulating, setSimulating] = useState(false);
  const [simResult, setSimResult] = useState(null);
  const [newCaseId, setNewCaseId] = useState(null);
  const [expandedMsg, setExpandedMsg] = useState(null);
  const highlightRef = useRef(null);

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (newCaseId && highlightRef.current) {
      highlightRef.current.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }
  }, [newCaseId, cases]);

  const fetchData = async () => {
    try {
      const [statsRes, casesRes] = await Promise.all([
        fetch(`${API_BASE}/stats`),
        fetch(`${API_BASE}/cases`),
      ]);
      setStats(await statsRes.json());
      setCases(await casesRes.json());
    } catch (err) {
      console.error('Fetch error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSimulate = async () => {
    setSimulating(true);
    setSimResult(null);
    setNewCaseId(null);
    try {
      const res = await fetch(`${API_BASE}/simulate`, { method: 'POST' });
      const data = await res.json();
      setSimResult(data.message);
      setNewCaseId(data.case_id);
      await fetchData();
    } catch (err) {
      setSimResult('Simulation failed. Is the backend running?');
    } finally {
      setSimulating(false);
    }
  };

  if (loading && !stats) {
    return (
      <div className="loading-screen">
        <div className="spinner" />
        <p>Connecting to Vasooli Control Tower...</p>
      </div>
    );
  }

  const avgScore = stats?.avg_recovery_score || 0;

  return (
    <div className="app">
      {/* Header */}
      <header className="header">
        <div className="header-left">
          <div className="logo">
            <div>
              <h1>Vasooli AI</h1>
              <p className="header-sub">Revenue Recovery Operations Center</p>
            </div>
          </div>
        </div>
        <div className="header-right">
          <span className="status-pill">Live</span>
          <button
            className={`simulate-btn ${simulating ? 'simulating' : ''}`}
            onClick={handleSimulate}
            disabled={simulating}
            id="simulate-payment-failure-btn"
          >
            {simulating ? (
              <><span className="btn-spinner" /> Running Pipeline...</>
            ) : (
              <>Simulate Payment Failure</>
            )}
          </button>
        </div>
      </header>

      {/* Simulation Result Toast */}
      {simResult && (
        <div className="sim-toast">
          <span>{simResult}</span>
          <button onClick={() => setSimResult(null)}>✕</button>
        </div>
      )}

      {/* Stats Grid */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-body">
            <div className="stat-label">Total Cases</div>
            <div className="stat-value">{stats?.total_cases?.toLocaleString() || 0}</div>
          </div>
        </div>
        <div className="stat-card stat-card--risk">
          <div className="stat-body">
            <div className="stat-label">Amount at Risk</div>
            <div className="stat-value">₹{(stats?.total_risk_inr || 0).toLocaleString()}</div>
          </div>
        </div>
        <div className="stat-card stat-card--recovered">
          <div className="stat-body">
            <div className="stat-label">Cash Recovered</div>
            <div className="stat-value green">₹{(stats?.total_cash_recovered_inr || 0).toLocaleString()}</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-body">
            <div className="stat-label">Payment Links Sent</div>
            <div className="stat-value">{stats?.success_links || 0}</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-body">
            <div className="stat-label">Avg Recovery Score</div>
            <div className={`stat-value ${avgScore >= 70 ? 'green' : avgScore >= 40 ? 'orange' : 'red'}`}>
              {avgScore}/100
            </div>
          </div>
        </div>
      </div>

      {/* AI Insights Panel */}
      <AIInsights cases={cases} />

      {/* Table */}
      <div className="table-wrapper">
        <div className="table-header">
          <h2>Recovery Cases <span className="case-count">{cases.length}</span></h2>
        </div>
        <div className="table-scroll">
          <table>
            <thead>
              <tr>
                <th>#</th>
                <th>Customer</th>
                <th>Amount</th>
                <th>Failure Reason</th>
                <th>Recovery Score</th>
                <th>AI Action</th>
                <th>Recovery Message</th>
                <th>Resource</th>
              </tr>
            </thead>
            <tbody>
              {cases.map((c) => {
                const isNew = c.case_id === newCaseId;
                return (
                  <tr
                    key={c.case_id}
                    ref={isNew ? highlightRef : null}
                    className={isNew ? 'row-highlight' : ''}
                  >
                    <td className="case-id">#{c.case_id}</td>
                    <td>
                      <div className="customer-cell">
                        <span className="customer-name">{c.customer_name}</span>
                        <span className="customer-email">{c.customer_email}</span>
                        {c.tenure_days && (
                          <span className="tenure-tag">{Math.round(c.tenure_days / 30)}mo</span>
                        )}
                      </div>
                    </td>
                    <td className="amount-cell">₹{c.amount_inr?.toLocaleString()}</td>
                    <td className="diagnosis-cell">
                      <span className="diagnosis-text">{c.diagnosis}</span>
                    </td>
                    <td>
                      <ScoreBadge score={c.recovery_score || 0} />
                    </td>
                    <td>
                      <ActionBadge action={c.policy_decision} />
                    </td>
                    <td className="message-cell">
                      {c.recovery_message ? (
                        <div className="message-wrap">
                          <span
                            className="message-preview"
                            onClick={() => setExpandedMsg(expandedMsg === c.case_id ? null : c.case_id)}
                          >
                            {expandedMsg === c.case_id
                              ? c.recovery_message
                              : c.recovery_message.slice(0, 60) + (c.recovery_message.length > 60 ? '...' : '')}
                          </span>
                          <CopyButton text={c.recovery_message} />
                        </div>
                      ) : (
                        <span className="no-msg">—</span>
                      )}
                    </td>
                    <td>
                      {c.payment_link_id ? (
                        <a
                          href={`https://dashboard.razorpay.com/app/paymentlinks/${c.payment_link_id}`}
                          target="_blank"
                          rel="noreferrer"
                          className="link-btn"
                        >
                          View Link
                        </a>
                      ) : (
                        <span className="no-link">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
              {cases.length === 0 && (
                <tr>
                  <td colSpan="8" className="empty-state">
                    No cases yet. Press "Simulate Payment Failure" to see the pipeline in action.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default App;
