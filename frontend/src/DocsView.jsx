import React from 'react';

export default function DocsView({ onGoToFaq, onGoToDashboard }) {
  return (
    <div className="docs-container">
      {/* Hero Banner */}
      <div className="docs-hero">
        <div className="docs-hero-badge">Razorpay AI Buildathon 2026 • Track 03: AI Revenue Recovery</div>
        <h1 className="docs-hero-title">Vasooli AI Architecture & System Blueprint</h1>
        <p className="docs-hero-desc">
          An Autonomous Merchant-Side Revenue Operations Agent that detects failed recurring subscription payments,
          diagnoses failure evidence, enforces deterministic financial guardrails, and executes bounded recovery workflows using Razorpay's API primitives.
        </p>
        <div className="docs-hero-actions">
          <button className="docs-btn docs-btn-primary" onClick={onGoToDashboard}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: '6px' }}>
              <rect x="3" y="3" width="7" height="9" />
              <rect x="14" y="3" width="7" height="5" />
              <rect x="14" y="12" width="7" height="9" />
              <rect x="3" y="16" width="7" height="5" />
            </svg>
            View Live Dashboard
          </button>
          <button className="docs-btn docs-btn-secondary" onClick={onGoToFaq}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: '6px' }}>
              <circle cx="12" cy="12" r="10" />
              <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
              <line x1="12" y1="17" x2="12.01" y2="17" />
            </svg>
            Open Interview FAQ
          </button>
        </div>
      </div>

      {/* Core Fact Banner */}
      <div className="doc-callout doc-callout-info">
        <div className="doc-callout-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#3182ce" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="16" x2="12" y2="12" />
            <line x1="12" y1="8" x2="12.01" y2="8" />
          </svg>
        </div>
        <div className="doc-callout-content">
          <h4>Core Architectural Fact: Who Are We Building For?</h4>
          <p>
            <strong>Vasooli AI is NOT an internal feature of Razorpay.</strong> It is an autonomous 
            <strong> Merchant-Side Operations Agent</strong> deployed by SaaS, EdTech, and subscription businesses who use Razorpay.
            Razorpay provides the neutral payment execution rail; Vasooli AI acts as the merchant's financial decision-maker.
          </p>
        </div>
      </div>

      {/* Grid: Problem & Solution */}
      <div className="docs-grid-two">
        <div className="doc-card">
          <div className="doc-card-header">
            <span className="doc-tag doc-tag-danger">The Problem</span>
            <h3>Involuntary Churn in Recurring Payments</h3>
          </div>
          <p className="doc-card-text">
            When merchants collect subscription fees via automated e-mandates, <strong>10% to 15% of recurring payments fail</strong>.
            Customers rarely intend to cancel; payments fail due to:
          </p>
          <ul className="doc-list">
            <li><strong>Temporary Core Banking Outages</strong> (Bank servers down)</li>
            <li><strong>Liquidity Crunches</strong> (Temporary low account balance)</li>
            <li><strong>Card Expiry / Mandate Cancellation</strong></li>
          </ul>
          <p className="doc-card-text" style={{ marginTop: '12px' }}>
            <strong>The Blind Retry Trap:</strong> Default payment systems repeatedly retry debiting the <em>full amount</em> (e.g. ₹999).
            When retries exhaust, the subscription moves to <code>HALTED</code>, and the merchant loses a loyal customer permanently.
          </p>
        </div>

        <div className="doc-card">
          <div className="doc-card-header">
            <span className="doc-tag doc-tag-success">The Solution</span>
            <h3>Intelligent Context-Aware Recovery</h3>
          </div>
          <p className="doc-card-text">
            Vasooli AI bridges the gap between a failed payment signal and a recovered rupee by evaluating customer context:
          </p>
          <ul className="doc-list">
            <li><strong>Bank Server Down?</strong> → <code>MONITOR</code> (Do not spam the customer; let native retry succeed).</li>
            <li><strong>Insufficient Funds?</strong> → <code>ONE_TIME_RECOVERY_PARTIAL</code> (Generate a 30% partial payment link of ₹333 on merchant's authority to recover cash and keep the account active).</li>
            <li><strong>High-Value Transaction (&gt;₹50,000)?</strong> → <code>ESCALATE</code> for human VIP review.</li>
            <li><strong>Customer Opted Out?</strong> → Hard <code>STOP</code> for 100% legal compliance.</li>
          </ul>
        </div>
      </div>

      {/* Comparison Matrix: Razorpay vs Vasooli AI */}
      <div className="doc-card doc-card-wide">
        <div className="doc-card-header">
          <span className="doc-tag doc-tag-primary">Positioning Matrix</span>
          <h3>Razorpay (Execution Rail) vs. Vasooli AI (Decision Orchestrator)</h3>
        </div>
        <div className="table-scroll">
          <table className="doc-comparison-table">
            <thead>
              <tr>
                <th>Capability / Responsibility</th>
                <th>Razorpay Default Engine</th>
                <th>Vasooli AI Operations Agent</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td><strong>Role & Analogy</strong></td>
                <td>Payment Gateway / Execution Rail (The Car's Engine & Wheels)</td>
                <td>Autonomous Merchant Revenue Manager (The Driver)</td>
              </tr>
              <tr>
                <td><strong>Authority Level</strong></td>
                <td>Neutral Processor (Cannot unilaterally alter contractual amounts)</td>
                <td>Merchant Representative (Holds private API keys to grant partial terms)</td>
              </tr>
              <tr>
                <td><strong>Low Balance Failure (₹999)</strong></td>
                <td>Blindly retries ₹999 at 24h/48h → Exhausts retries → Halts subscription</td>
                <td>Analyzes customer tenure → Generates 30% Partial Link (₹333) with empathetic note</td>
              </tr>
              <tr>
                <td><strong>Temporary Bank Decline</strong></td>
                <td>Sends blunt failure notification email to customer</td>
                <td>Selects <code>MONITOR</code> to avoid customer annoyance during outages</td>
              </tr>
              <tr>
                <td><strong>Customer LTV & Tenure</strong></td>
                <td>Treats all subscriptions with the same standardized retry schedule</td>
                <td>Computes recovery score (0–100) based on tenure, history, and amount</td>
              </tr>
              <tr>
                <td><strong>High-Value Guardrails</strong></td>
                <td>No automated escalation threshold for ops review</td>
                <td>Deterministic policy overrides AI above ₹50,000 to trigger VIP human contact</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* 7-Step Architecture Flow */}
      <div className="doc-card doc-card-wide">
        <div className="doc-card-header">
          <span className="doc-tag doc-tag-primary">Engineering Lifecycle</span>
          <h3>The 7-Step Closed-Loop Architecture</h3>
        </div>
        <div className="pipeline-steps">
          <div className="pipeline-step">
            <div className="step-num">1</div>
            <div className="step-info">
              <h4>Detect</h4>
              <p>Simulated or real Razorpay Test Mode subscription payment failure generates webhook event.</p>
            </div>
          </div>
          <div className="pipeline-step">
            <div className="step-num">2</div>
            <div className="step-info">
              <h4>Ingest & Secure</h4>
              <p>HMAC-SHA256 signature verification, <code>x-razorpay-event-id</code> deduplication, and SQLite concurrency lock management.</p>
            </div>
          </div>
          <div className="pipeline-step">
            <div className="step-num">3</div>
            <div className="step-info">
              <h4>State Reconciliation</h4>
              <p>Tolerates out-of-order webhooks by reconciling with authoritative Razorpay provider state before updating projections.</p>
            </div>
          </div>
          <div className="pipeline-step">
            <div className="step-num">4</div>
            <div className="step-info">
              <h4>Diagnose & Decide</h4>
              <p>Gemini 3.7 Flash evaluates failure metadata and tenure to generate a structured JSON recommendation (Non-Authoritative).</p>
            </div>
          </div>
          <div className="pipeline-step">
            <div className="step-num">5</div>
            <div className="step-info">
              <h4>Deterministic Policy Engine</h4>
              <p>Hardcoded business rules validate and approve action. Enforces 50k limit, opt-out stops, and unknown signal fallbacks.</p>
            </div>
          </div>
          <div className="pipeline-step">
            <div className="step-num">6</div>
            <div className="step-info">
              <h4>Execute</h4>
              <p>Invokes Razorpay Payment Links API with <code>accept_partial=True</code> and 33% minimum amount when appropriate.</p>
            </div>
          </div>
          <div className="pipeline-step">
            <div className="step-num">7</div>
            <div className="step-info">
              <h4>Verify & Measure</h4>
              <p>Listens for <code>payment_link.paid</code> webhook, marks case <code>RECOVERED</code>, and honestly separates Cash Recovered from Subscription Reactivated.</p>
            </div>
          </div>
        </div>
      </div>

      {/* Safety & Compliance Card */}
      <div className="doc-card doc-card-wide">
        <div className="doc-card-header">
          <span className="doc-tag doc-tag-warning">Enterprise Trust & Safety</span>
          <h3>The Bounded AI Philosophy (Why LLMs Never Directly Touch Money)</h3>
        </div>
        <p className="doc-card-text">
          In financial systems, probabilistic models (LLMs) must never possess autonomous authority to move funds or alter business limits.
          Vasooli AI enforces strict separation between <strong>AI Advisory Reasoning</strong> and <strong>Deterministic Financial Policies</strong>:
        </p>
        <div className="guardrails-grid">
          <div className="guardrail-box">
            <div className="guardrail-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#e53e3e" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="7.86 2 16.14 2 22 7.86 22 16.14 16.14 22 7.86 22 2 16.14 2 7.86 7.86 2" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
            </div>
            <h5>Rule 1: Customer Opt-Out / Mandate Cancel</h5>
            <p>If customer has revoked auto-pay permission, the Policy Engine immediately triggers <code>STOP</code>. No payment link is ever generated.</p>
          </div>
          <div className="guardrail-box">
            <div className="guardrail-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#dd6b20" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
                <line x1="12" y1="9" x2="12" y2="13" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
            </div>
            <h5>Rule 2: High-Value Threshold (&gt; ₹50,000)</h5>
            <p>High-value accounts require human care. Any transaction above ₹50,000 is automatically overridden to <code>ESCALATE</code>.</p>
          </div>
          <div className="guardrail-box">
            <div className="guardrail-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#3182ce" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" />
                <line x1="12" y1="17" x2="12.01" y2="17" />
              </svg>
            </div>
            <h5>Rule 3: Unknown or Conflicting Signals</h5>
            <p>When failure metadata is ambiguous, the system refuses to invent a reason. It tags <code>UNKNOWN</code> and routes to human ops.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
