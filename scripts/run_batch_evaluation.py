"""
Vasooli Batch Evaluation Script (Step 7)
=========================================
Self-contained batch evaluation that:
1. Generates 500 synthetic failed payment records
2. Runs deterministic AI Diagnosis and Policy Engine logic INLINE
3. Simulates action execution WITHOUT calling Razorpay API
4. Generates final_metrics.md report

Seed: 20260821 (fixed for reproducibility)
"""
import sys
import os
import sqlite3
import random
import uuid
import json
from datetime import datetime

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.database import DB_PATH, init_db

SEED = 20260821
TOTAL_RECORDS = 500
HIGH_VALUE_THRESHOLD = 5000000  # 50,000 INR in paise

# ---------------------------------------------------------------------------
# Inline deterministic AI Diagnosis (no LLM API call)
# ---------------------------------------------------------------------------
def inline_diagnose(raw_diagnosis: str) -> dict:
    """Mimics the policy engine's diagnostic scoring without any API calls."""
    reason = "UNKNOWN"
    score = 50

    if "insufficient_funds" in raw_diagnosis:
        reason = "INSUFFICIENT_FUNDS"
        score = 85
    elif "card_expired" in raw_diagnosis:
        reason = "CARD_EXPIRED"
        score = 20
    elif "bank_decline" in raw_diagnosis:
        reason = "BANK_DECLINE"
        score = 90
    elif "customer_cancelled" in raw_diagnosis:
        reason = "MANDATE_CANCELLED"
        score = 5
    elif "unknown_error" in raw_diagnosis:
        reason = "UNKNOWN"
        score = 40

    recommended_action = "ESCALATE"
    if reason in ("INSUFFICIENT_FUNDS", "BANK_DECLINE") and score >= 70:
        recommended_action = "ONE_TIME_RECOVERY"
    elif reason in ("MANDATE_CANCELLED",):
        recommended_action = "STOP"
    elif reason == "CARD_EXPIRED":
        recommended_action = "STOP"
    elif reason == "UNKNOWN":
        recommended_action = "ESCALATE"

    return {
        "reason": reason,
        "confidence": score,
        "recommended_action": recommended_action,
        "explanation": f"Batch evaluation: {reason} (score={score})"
    }

# ---------------------------------------------------------------------------
# Inline deterministic Policy Engine
# ---------------------------------------------------------------------------
def inline_policy(amount: int, ai_rec: dict, opt_out: bool, sub_state: str) -> tuple:
    ai_action = ai_rec.get("recommended_action", "ESCALATE")
    
    if opt_out:
        return "STOP", "Rule 1: customer_opt_out=True"
    if sub_state == "cancelled":
        return "STOP", "Rule 4: subscription cancelled"
    if amount > HIGH_VALUE_THRESHOLD:
        return "ESCALATE", "Rule 6: amount > INR 50,000 threshold"
    if ai_action not in ["MONITOR", "ESCALATE", "STOP", "ONE_TIME_RECOVERY", "PAYMENT_METHOD_RECOVERY"]:
        return "ESCALATE", f"Rule 7: unsupported action ({ai_action})"
    
    return ai_action, None

# ---------------------------------------------------------------------------
# Main Batch Runner
# ---------------------------------------------------------------------------
def run_batch():
    print(f"Starting Vasooli Batch Evaluation (Dry Run, Seed={SEED})...")
    init_db()
    random.seed(SEED)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    reasons = [
        "insufficient_funds: The customer's bank account does not have enough balance.",
        "card_expired: The card used for the mandate has expired.",
        "bank_decline: Temporary bank server outage.",
        "customer_cancelled: The customer explicitly revoked the mandate.",
        "unknown_error: Unrecognized gateway code 9982."
    ]

    amounts = [49900, 99900, 199900, 500000, 8000000]  # Last is high-value (>50k)
    
    # Track case IDs created in this run
    cases = []

    for i in range(TOTAL_RECORDS):
        cust_id = f"cust_eval_{SEED}_{i}"
        sub_id  = f"sub_eval_{SEED}_{i}"
        amount  = random.choice(amounts)
        reason  = random.choice(reasons)
        opt_out = "customer_cancelled" in reason  # Simulate opt-out

        # Upsert customer
        cursor.execute('''
            INSERT INTO customers (external_id, name, email, contact, tenure_days, opt_out)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(external_id) DO UPDATE SET opt_out=excluded.opt_out
        ''', (cust_id, f"Eval User {i}", f"eval{i}@batch.test", "+919876543210", 30, int(opt_out)))

        cursor.execute('SELECT id FROM customers WHERE external_id = ?', (cust_id,))
        cust_pk = cursor.fetchone()[0]

        # Upsert subscription
        cursor.execute('''
            INSERT INTO subscriptions (external_id, customer_id, plan_id, amount, state)
            VALUES (?, ?, 'plan_eval', ?, 'halted')
            ON CONFLICT(external_id) DO UPDATE SET amount=excluded.amount
        ''', (sub_id, cust_pk, amount))

        cursor.execute('SELECT id FROM subscriptions WHERE external_id = ?', (sub_id,))
        sub_pk = cursor.fetchone()[0]

        # Create recovery case
        cursor.execute('''
            INSERT INTO recovery_cases (subscription_id, customer_id, amount_at_risk, status, priority, diagnosis)
            VALUES (?, ?, ?, 'AT_RISK', 'MEDIUM', ?)
        ''', (sub_pk, cust_pk, amount, reason))
        case_id = cursor.lastrowid
        cases.append((case_id, amount, reason, opt_out))

    conn.commit()
    print(f"Generated {TOTAL_RECORDS} cases. Running AI Diagnosis & Policy Engine...")

    # --- Phase 2: Run pipeline ---
    stats = {
        "MONITOR": 0, "ONE_TIME_RECOVERY": 0, "ESCALATE": 0,
        "STOP": 0, "NO_ACTION": 0
    }
    risk_by_action = {k: 0 for k in stats}
    recovered_amount = 0
    recovery_count = 0

    for idx, (case_id, amount, reason, opt_out) in enumerate(cases):
        # Inline AI diagnosis
        ai_rec = inline_diagnose(reason)
        ai_rec_json = json.dumps(ai_rec)

        # Inline policy decision
        final_decision, override_reason = inline_policy(amount, ai_rec, opt_out, "halted")

        # Persist decision
        cursor.execute('''
            UPDATE recovery_cases
            SET ai_recommendation = ?, policy_decision = ?, policy_override_reason = ?, status = 'ACTION_APPROVED'
            WHERE id = ?
        ''', (ai_rec_json, final_decision, override_reason, case_id))

        # Persist action record
        cursor.execute('''
            INSERT INTO recovery_actions (case_id, action_type, status, ai_recommended, policy_approved, reason)
            VALUES (?, ?, 'PENDING', ?, ?, ?)
        ''', (case_id, final_decision, ai_rec["recommended_action"] == final_decision, True, override_reason or "AI Approved"))
        action_id = cursor.lastrowid

        stats[final_decision] = stats.get(final_decision, 0) + 1
        risk_by_action[final_decision] = risk_by_action.get(final_decision, 0) + amount

        # --- Phase 3: Simulate execution (no real Razorpay API) ---
        if final_decision == "ONE_TIME_RECOVERY":
            mock_plink_id = f"plink_batch_{uuid.uuid4().hex[:10]}"
            cursor.execute('''
                UPDATE recovery_actions
                SET status = 'COMPLETED', razorpay_resource_id = ?, executed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (mock_plink_id, action_id))

            # Simulate 60% payment success rate
            if random.random() < 0.6:
                cursor.execute("UPDATE recovery_cases SET status = 'RECOVERED' WHERE id = ?", (case_id,))
                cursor.execute('''
                    INSERT INTO recovery_outcomes (case_id, action_id, cash_recovered, cash_amount)
                    VALUES (?, ?, 1, ?)
                ''', (case_id, action_id, amount))
                recovered_amount += amount
                recovery_count += 1
        else:
            cursor.execute('''
                UPDATE recovery_actions
                SET status = 'COMPLETED', executed_at = CURRENT_TIMESTAMP WHERE id = ?
            ''', (action_id,))

        if (idx + 1) % 100 == 0:
            print(f"Processed {idx+1}/{TOTAL_RECORDS}...")

    conn.commit()
    conn.close()

    print("Pipeline Execution Completed.")

    # --- Phase 4: Generate Report ---
    total_risk = sum(a for _, a, _, _ in cases)
    recovery_rate = (recovered_amount / total_risk * 100) if total_risk else 0
    one_time_cases = stats.get("ONE_TIME_RECOVERY", 0)
    paid_links = recovery_count

    reports_dir = os.path.join(os.path.dirname(__file__), '..', 'reports')
    os.makedirs(reports_dir, exist_ok=True)

    metrics_path = os.path.join(reports_dir, 'final_metrics.md')
    with open(metrics_path, 'w', encoding='utf-8') as f:
        f.write("# Vasooli — Final Batch Evaluation Metrics\n\n")
        f.write(f"| Parameter | Value |\n|---|---|\n")
        f.write(f"| Dataset | {TOTAL_RECORDS} synthetic records |\n")
        f.write(f"| Random Seed | {SEED} |\n")
        f.write(f"| Policy Version | v1.0 |\n")
        f.write(f"| Evaluation Date | {datetime.now().strftime('%Y-%m-%d')} |\n")
        f.write(f"| Razorpay API Calls | 0 (dry run, mocked) |\n\n")

        f.write("## Executive Summary\n\n")
        f.write(f"| Metric | Value |\n|---|---|\n")
        f.write(f"| Total Revenue at Risk | ₹{total_risk/100:,.2f} |\n")
        f.write(f"| Verified Cash Recovered | ₹{recovered_amount/100:,.2f} |\n")
        f.write(f"| Cash Recovery Rate | {recovery_rate:.2f}% |\n")
        f.write(f"| Payment Links Generated | {one_time_cases} |\n")
        f.write(f"| Payment Links Paid (simulated 60%) | {paid_links} |\n")
        f.write(f"| Unrecovered Revenue | ₹{(total_risk - recovered_amount)/100:,.2f} |\n\n")

        f.write("## Action Breakdown\n\n")
        f.write("| Action | Cases | Revenue at Risk | Notes |\n|---|---:|---:|---|\n")
        for action, count in stats.items():
            risk = risk_by_action.get(action, 0)
            notes = ""
            if action == "ONE_TIME_RECOVERY":
                notes = f"{paid_links} paid (simulated)"
            elif action == "ESCALATE":
                notes = "Includes high-value + UNKNOWN"
            elif action == "STOP":
                notes = "Customer cancelled / opt-out"
            f.write(f"| {action} | {count} | ₹{risk/100:,.2f} | {notes} |\n")

        f.write("\n## Exception Analysis\n\n")
        f.write("Every case with no verified cash recovery is classified below.\n\n")
        f.write("| Reason | Cases |\n|---|---:|\n")
        stop_count = stats.get("STOP", 0)
        escalate_count = stats.get("ESCALATE", 0)
        unrecovered_links = one_time_cases - paid_links
        f.write(f"| CUSTOMER_CANCELLED / OPT_OUT | {stop_count} |\n")
        f.write(f"| UNKNOWN / INSUFFICIENT_EVIDENCE → Escalated | {escalate_count} |\n")
        f.write(f"| PAYMENT_NOT_COMPLETED (link not paid) | {unrecovered_links} |\n\n")

        f.write("## Known Limitations\n\n")
        f.write("- This evaluation uses a **synthetic dataset** (not real Razorpay transactions).\n")
        f.write("- Razorpay API calls were **mocked** to avoid test-mode rate limits.\n")
        f.write("- The 60% payment success rate is a simulation — real rates vary by customer segment.\n")
        f.write("- Manual charge (MANUAL_CHARGE) action is excluded from this batch.\n")
        f.write("- Subscription reactivation rate is not measured separately (requires live webhooks).\n")

    print(f"Report saved: {metrics_path}")
    
    # Summary to console
    print("\n" + "="*50)
    print(f"BATCH EVALUATION COMPLETE")
    print(f"{'='*50}")
    print(f"Records Processed : {TOTAL_RECORDS}")
    print(f"Revenue at Risk   : Rs {total_risk/100:,.2f}")
    print(f"Cash Recovered    : Rs {recovered_amount/100:,.2f}")
    print(f"Recovery Rate     : {recovery_rate:.2f}%")
    print(f"Action Summary    : {dict(stats)}")
    print("="*50)

if __name__ == "__main__":
    run_batch()
