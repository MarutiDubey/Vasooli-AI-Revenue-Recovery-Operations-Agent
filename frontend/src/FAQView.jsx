import React, { useState } from 'react';

const FAQ_DATA = [
  {
    id: 'q1',
    category: 'Architecture',
    question: 'What is a Webhook and why don\'t we use standard API polling?',
    answer: (
      <div>
        <p>A Webhook is an event-driven <strong>"Call Me Back"</strong> mechanism (Reverse API):</p>
        <ul>
          <li>
            <strong>Drawback of Polling:</strong> If our server continuously called the Razorpay API every 5 seconds asking 
            <em>"Did any subscription charge fail?"</em>, it would create thousands of wasteful network requests and overload both servers.
          </li>
          <li>
            <strong>Webhook Efficiency (The Pizza Delivery Analogy):</strong> When you order pizza, you don't call the shop every 60 seconds asking if it's ready. Instead, the shop sends you an automated SMS when it's out for delivery. Similarly, Razorpay automatically pushes a POST request containing the failure payload to our <code>/webhook/razorpay</code> endpoint the exact millisecond a payment fails.
          </li>
        </ul>
      </div>
    )
  },
  {
    id: 'q2',
    category: 'Security',
    question: 'How does HMAC-SHA256 signature verification protect against webhook spoofing?',
    answer: (
      <div>
        <p>Because our webhook endpoint is exposed to the public internet, any malicious party could attempt to inject fake failure payloads. We prevent this using cryptographic signature verification:</p>
        <ol>
          <li>
            <strong>Shared Secret:</strong> A secret key known exclusively to Razorpay and our backend environment (<code>RAZORPAY_WEBHOOK_SECRET</code>).
          </li>
          <li>
            <strong>Signature Generation:</strong> Razorpay hashes the raw request body bytes and the secret key using the <code>HMAC-SHA256</code> algorithm and attaches the digest in the <code>x-razorpay-signature</code> header.
          </li>
          <li>
            <strong>Constant-Time Verification:</strong> Our server recomputes the HMAC digest over the raw incoming bytes and verifies it using Python's <code>hmac.compare_digest</code> to prevent timing attacks. If the digest does not match 100%, the request is immediately rejected with HTTP 400 Bad Request.
          </li>
        </ol>
      </div>
    )
  },
  {
    id: 'q3',
    category: 'Architecture',
    question: 'Why explicitly close the database connection (conn.close()) before calling the AI?',
    answer: (
      <div>
        <p>This is a critical concurrency optimization for SQLite:</p>
        <ul>
          <li>
            <strong>SQLite Write-Lock Behavior:</strong> When SQLite writes a new record, it acquires an exclusive file lock on the database.
          </li>
          <li>
            <strong>LLM Latency:</strong> An external AI inference call (Gemini 3.7 Flash) typically takes 2 to 3 seconds to process evidence and format JSON.
          </li>
          <li>
            <strong>The Concurrency Trap:</strong> If we held the database connection open during the 3-second AI call, the entire database would remain locked. Any new webhooks arriving during that window would crash with <code>OperationalError: database is locked</code>, causing Razorpay delivery timeouts.
          </li>
          <li>
            <strong>The Fix:</strong> We insert the raw event, immediately call <code>conn.close()</code> to release the lock, return a fast <code>200 OK</code> to Razorpay, and then execute the AI analysis freely in the background.
          </li>
        </ul>
      </div>
    )
  },
  {
    id: 'q4',
    category: 'Strategy & Positioning',
    question: 'Razorpay already retries payments and supports partial links. Is Vasooli AI duplicate?',
    answer: (
      <div>
        <p>This is the single most important architectural distinction to understand:</p>
        <div className="doc-callout doc-callout-info" style={{ margin: '10px 0' }}>
          <strong>The Analogy:</strong> Razorpay provides the car's engine, wheels, and transmission (Execution Rail). Vasooli AI is the driver steering the vehicle (Decision Orchestration Layer).
        </div>
        <ul>
          <li>
            <strong>Default Engine Limitation:</strong> If a customer with low balance fails a ₹999 payment, Razorpay blindly retries debiting the full ₹999 at 24h and 48h intervals. Once exhausted, the subscription becomes <code>HALTED</code> and the customer is lost. Razorpay never automatically decomposes ₹999 into a 30% partial payment link.
          </li>
          <li>
            <strong>Operational Scale:</strong> A merchant with 10,000 subscriptions faces 1,500 monthly payment failures. No human ops team can manually inspect 1,500 webhooks to construct bespoke partial links. Vasooli AI autonomously evaluates tenure, failure reasons, and financial guardrails in real time.
          </li>
        </ul>
      </div>
    )
  },
  {
    id: 'q5',
    category: 'Compliance & Privacy',
    question: 'How do we know a customer has low balance? Do we inspect their bank account balance?',
    answer: (
      <div>
        <p><strong>Absolutely NOT.</strong> In strict accordance with banking privacy and BFSI compliance:</p>
        <div className="doc-callout doc-callout-warning" style={{ margin: '10px 0' }}>
          <em>"We never access or infer the customer's exact bank balance. We do not know whether the customer has ₹10 or ₹500 in their account."</em>
        </div>
        <p>
          Instead, when an auto-debit fails, the issuing bank returns structured failure metadata in the transaction payload:
          <code>error_source: "bank"</code>, <code>error_reason: "payment_failed"</code>, and 
          <code>error_description: "Payment failed due to insufficient funds in customer bank account"</code>.
        </p>
        <p>
          Our normalizer converts this bank-confirmed decline code into an internal diagnosis of <code>INSUFFICIENT_FUNDS</code>.
          We do not query bank balances; we evaluate the bank's authoritative decline code alongside customer tenure to formulate a flexible recovery offer.
        </p>
      </div>
    )
  },
  {
    id: 'q6',
    category: 'Strategy & Positioning',
    question: 'Can Razorpay send partial payment offers itself? Why does the merchant have authority?',
    answer: (
      <div>
        <ol>
          <li>
            <strong>Why Razorpay CANNOT do this:</strong> Razorpay is a neutral payment gateway. If Razorpay unilaterally discounted a merchant's ₹999 subscription to ₹333, the merchant would sue Razorpay for altering contractual pricing without consent! Razorpay's default retry engine is legally bound to attempt the full contractual amount.
          </li>
          <li>
            <strong>Why Vasooli AI CAN do this:</strong> Because Vasooli AI operates <strong>on behalf of the Merchant</strong> using the merchant's authorized private API keys (<code>RAZORPAY_KEY_ID</code>, <code>RAZORPAY_KEY_SECRET</code>). The merchant owns the business and possesses the full commercial right to offer flexible terms to retain valuable customers.
          </li>
        </ol>
      </div>
    )
  },
  {
    id: 'q7',
    category: 'Strategy & Positioning',
    question: 'Who is the primary user of Vasooli AI? (Merchant vs Razorpay)',
    answer: (
      <div>
        <p>
          <strong>The user is the Merchant (SaaS Founder, EdTech Company, or their Finance/Operations team)</strong> who collects subscription payments via Razorpay.
        </p>
        <p>
          Vasooli AI is not an internal core banking tool deployed at Razorpay headquarters; it is a merchant-side operations platform that turns failed payment signals into verified, recovered cash.
        </p>
      </div>
    )
  },
  {
    id: 'q8',
    category: 'AI & Policy',
    question: 'Why use Gemini 3.7 Flash instead of OpenAI GPT-4?',
    answer: (
      <div>
        <p>Two critical reasons: <strong>Reasoning Capability</strong> and <strong>Cost at Scale</strong>.</p>
        <ul>
          <li>
            <strong>Reasoning Quality:</strong> Gemini 3.7 Flash combines cutting-edge chain-of-thought reasoning with blazing-fast inference, perfectly understanding payment failure evidence.
          </li>
          <li>
            <strong>Structured Instruction-Following:</strong> Gemini 3.7 Flash excels at extracting parameters and outputting strict, deterministic JSON without unpredictable chatty preambles.
          </li>
          <li>
            <strong>Economic Viability:</strong> At a scale of 10,000+ failed payment webhooks per month, Gemini 3.7 Flash provides enterprise-grade reasoning with maximum cost efficiency.
          </li>
        </ul>
      </div>
    )
  },
  {
    id: 'q9',
    category: 'Architecture',
    question: 'How does the system handle duplicate webhooks? (Idempotency)',
    answer: (
      <div>
        <p>Due to internet retries or gateway timeouts, Razorpay may transmit the exact same failure event twice.</p>
        <ul>
          <li>Every Razorpay event includes a unique <code>x-razorpay-event-id</code>.</li>
          <li>Our SQLite table <code>webhook_events</code> enforces a <code>UNIQUE</code> constraint on this event ID column.</li>
          <li>When a duplicate arrives, the database throws an <code>IntegrityError</code>. Our ingestion layer catches this exception, halts further workflow execution, and immediately returns a safe <code>200 OK</code> so Razorpay stops retrying.</li>
          <li>This mathematically guarantees that no customer ever receives duplicate payment links or duplicate messages.</li>
        </ul>
      </div>
    )
  },
  {
    id: 'q10',
    category: 'Architecture',
    question: 'How does the system tolerate out-of-order webhook delivery? (State Reconciliation)',
    answer: (
      <div>
        <p>Payment webhooks do not always arrive in the order they occurred. For instance, a <code>subscription.charged</code> event might arrive before a delayed <code>subscription.pending</code> event.</p>
        <p>
          Our state mapper does not blindly assume arrival sequence equals business truth. Before updating a subscription projection, it checks local state versioning. If an incoming event appears stale or contradictory, it performs a live reconciliation query against Razorpay's API to ensure the local database reflects authoritative ground truth.
        </p>
      </div>
    )
  },
  {
    id: 'q11',
    category: 'Compliance & Privacy',
    question: 'What is Honest Recovery Accounting? Why separate Cash Recovered from Subscription Reactivated?',
    answer: (
      <div>
        <p>A core differentiator demanded by Track 03 is <strong>Honest Financial Accounting</strong>:</p>
        <ul>
          <li>
            <strong>₹ Cash Recovered:</strong> When a customer pays a one-time partial recovery link (e.g. ₹333), the merchant has physically recovered cash. That is credited to <em>Cash Recovered</em>.
          </li>
          <li>
            <strong>₹ Subscription Revenue Reactivated:</strong> Paying a one-time Payment Link does NOT automatically restore the recurring bank e-mandate in Razorpay.
          </li>
          <li>
            <strong>Zero Conflation:</strong> Vasooli AI never claims a one-time cash recovery has magically reactivated recurring revenue. Both numbers are reported independently and transparently on the dashboard.
          </li>
        </ul>
      </div>
    )
  }
];

export default function FAQView({ onGoToDocs, onGoToDashboard }) {
  const [selectedCategory, setSelectedCategory] = useState('All');
  const [searchQuery, setSearchQuery] = useState('');
  const [openFaq, setOpenFaq] = useState('q1'); // Open first by default

  const categories = ['All', 'Architecture', 'Security', 'Strategy & Positioning', 'AI & Policy', 'Compliance & Privacy'];

  const filteredFaqs = FAQ_DATA.filter((faq) => {
    const matchesCategory = selectedCategory === 'All' || faq.category === selectedCategory;
    const matchesSearch = 
      faq.question.toLowerCase().includes(searchQuery.toLowerCase()) ||
      faq.category.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const toggleFaq = (id) => {
    setOpenFaq(openFaq === id ? null : id);
  };

  return (
    <div className="faq-container">
      {/* Header */}
      <div className="faq-header">
        <div className="faq-badge">Technical Viva & Interview Defense</div>
        <h2>Frequently Asked Questions & Architectural Deep-Dive</h2>
        <p>
          Clear, bulletproof answers to technical, operational, and financial questions for Razorpay judges, interviewers, and tech leads.
        </p>
      </div>

      {/* Search & Categories */}
      <div className="faq-controls">
        <div className="faq-search-wrapper">
          <span className="faq-search-icon">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
          </span>
          <input
            type="text"
            className="faq-search-input"
            placeholder="Search questions by keyword (e.g. idempotency, balance, security, partial)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
          {searchQuery && (
            <button className="faq-search-clear" onClick={() => setSearchQuery('')}>✕</button>
          )}
        </div>

        <div className="faq-category-pills">
          {categories.map((cat) => (
            <button
              key={cat}
              className={`category-pill ${selectedCategory === cat ? 'active' : ''}`}
              onClick={() => setSelectedCategory(cat)}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Accordion List */}
      <div className="faq-accordion-list">
        {filteredFaqs.length === 0 ? (
          <div className="faq-empty">
            <p>No questions found matching "{searchQuery}".</p>
            <button className="docs-btn docs-btn-secondary" onClick={() => { setSearchQuery(''); setSelectedCategory('All'); }}>
              Reset Filters
            </button>
          </div>
        ) : (
          filteredFaqs.map((faq, index) => {
            const isOpen = openFaq === faq.id;
            return (
              <div key={faq.id} className={`faq-accordion-item ${isOpen ? 'open' : ''}`}>
                <div 
                  className="faq-question-row" 
                  onClick={() => toggleFaq(faq.id)}
                  role="button"
                  tabIndex={0}
                  onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') toggleFaq(faq.id); }}
                >
                  <div className="faq-q-left">
                    <span className="faq-index">Q{index + 1}</span>
                    <span className="faq-q-text">{faq.question}</span>
                  </div>
                  <div className="faq-q-right">
                    <span className="faq-cat-badge">{faq.category}</span>
                    <span className={`faq-toggle-icon ${isOpen ? 'rotated' : ''}`}>
                      {isOpen ? '−' : '+'}
                    </span>
                  </div>
                </div>

                {isOpen && (
                  <div className="faq-answer-content">
                    {faq.answer}
                  </div>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Bottom CTA */}
      <div className="faq-footer-cta">
        <p>Want to see the system in action or review the complete technical blueprint?</p>
        <div style={{ display: 'flex', gap: '12px' }}>
          <button className="docs-btn docs-btn-primary" onClick={onGoToDashboard}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: '6px' }}>
              <rect x="3" y="3" width="7" height="9" />
              <rect x="14" y="3" width="7" height="5" />
              <rect x="14" y="12" width="7" height="9" />
              <rect x="3" y="16" width="7" height="5" />
            </svg>
            Go to Live Dashboard
          </button>
          <button className="docs-btn docs-btn-secondary" onClick={onGoToDocs}>
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: '6px' }}>
              <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
              <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
            </svg>
            View System Architecture
          </button>
        </div>
      </div>
    </div>
  );
}
