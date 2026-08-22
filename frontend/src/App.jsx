import { useState, useEffect } from 'react';
import './index.css';

const API_BASE = 'http://localhost:8000/api';

function App() {
  const [stats, setStats] = useState(null);
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchData();
    // Auto refresh every 5 seconds for demo purposes
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      const statsRes = await fetch(`${API_BASE}/stats`);
      const statsData = await statsRes.json();
      setStats(statsData);

      const casesRes = await fetch(`${API_BASE}/cases`);
      const casesData = await casesRes.json();
      setCases(casesData);
    } catch (error) {
      console.error("Error fetching dashboard data:", error);
    } finally {
      setLoading(false);
    }
  };

  const getPriorityBadge = (priority) => {
    switch (priority) {
      case 'HIGH': return 'badge badge-danger';
      case 'MEDIUM': return 'badge badge-warning';
      case 'LOW': return 'badge badge-info';
      default: return 'badge badge-info';
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'COMPLETED': return 'badge badge-success';
      case 'PENDING': return 'badge badge-warning';
      case 'FAILED': return 'badge badge-danger';
      default: return 'badge badge-info';
    }
  };

  if (loading && !stats) return <div style={{ padding: '2rem' }}>Loading Control Tower...</div>;

  return (
    <div className="dashboard-container">
      <header className="header">
        <h1>Vasooli Control Tower</h1>
        <div>
          <span className="badge badge-success" style={{ marginRight: '10px' }}>Backend Connected</span>
        </div>
      </header>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-title">Total Recovery Cases</div>
          <div className="stat-value">{stats?.total_cases || 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-title">Amount At Risk (INR)</div>
          <div className="stat-value">₹{(stats?.total_risk_inr || 0).toLocaleString()}</div>
        </div>
        <div className="stat-card">
          <div className="stat-title">Payment Links Generated</div>
          <div className="stat-value">{stats?.success_links || 0}</div>
        </div>
        <div className="stat-card">
          <div className="stat-title">Cash Recovered (INR)</div>
          <div className="stat-value" style={{color: 'var(--success-color)'}}>₹{(stats?.total_cash_recovered_inr || 0).toLocaleString()}</div>
        </div>
      </div>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>Customer</th>
              <th>Amount</th>
              <th>AI Diagnosis</th>
              <th>Action</th>
              <th>Status</th>
              <th>Resource</th>
            </tr>
          </thead>
          <tbody>
            {cases.map((c) => (
              <tr key={c.case_id}>
                <td>
                  <div className="customer-info">
                    <span className="customer-name">{c.customer_name}</span>
                    <span className="customer-email">{c.customer_email}</span>
                  </div>
                </td>
                <td style={{ fontWeight: 500 }}>₹{c.amount_inr.toLocaleString()}</td>
                <td>
                  <div style={{ marginBottom: '4px' }}>
                    <span className={getPriorityBadge(c.priority)}>{c.priority}</span>
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {c.diagnosis}
                  </div>
                </td>
                <td>
                  <span className="badge badge-info">{c.policy_decision}</span>
                </td>
                <td>
                  {c.action_status ? (
                    <span className={getStatusBadge(c.action_status)}>{c.action_status}</span>
                  ) : (
                    <span className="badge badge-info">{c.case_status}</span>
                  )}
                </td>
                <td>
                  {c.payment_link_id ? (
                    <a 
                      href={`https://dashboard.razorpay.com/app/paymentlinks/${c.payment_link_id}`} 
                      target="_blank" 
                      rel="noreferrer"
                      className="btn-primary"
                    >
                      View Link
                    </a>
                  ) : (
                    <span style={{ color: 'var(--text-muted)', fontSize: '0.75rem' }}>-</span>
                  )}
                </td>
              </tr>
            ))}
            {cases.length === 0 && (
              <tr>
                <td colSpan="6" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '3rem' }}>
                  No recovery cases found. Trigger a webhook to see data.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default App;
