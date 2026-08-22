# Vasooli — Final Batch Evaluation Metrics

| Parameter | Value |
|---|---|
| Dataset | 500 synthetic records |
| Random Seed | 20260821 |
| Policy Version | v1.0 |
| Evaluation Date | 2026-08-22 |
| Razorpay API Calls | 0 (dry run, mocked) |

## Executive Summary

| Metric | Value |
|---|---|
| Total Revenue at Risk | ₹8,440,677.00 |
| Verified Cash Recovered | ₹191,930.00 |
| Cash Recovery Rate | 2.27% |
| Payment Links Generated | 149 |
| Payment Links Paid (simulated 60%) | 90 |
| Unrecovered Revenue | ₹8,248,747.00 |

## Action Breakdown

| Action | Cases | Revenue at Risk | Notes |
|---|---:|---:|---|
| MONITOR | 0 | ₹0.00 |  |
| ONE_TIME_RECOVERY | 149 | ₹286,880.00 | 90 paid (simulated) |
| ESCALATE | 165 | ₹6,570,936.00 | Includes high-value + UNKNOWN |
| STOP | 186 | ₹1,582,861.00 | Customer cancelled / opt-out |
| NO_ACTION | 0 | ₹0.00 |  |

## Exception Analysis

Every case with no verified cash recovery is classified below.

| Reason | Cases |
|---|---:|
| CUSTOMER_CANCELLED / OPT_OUT | 186 |
| UNKNOWN / INSUFFICIENT_EVIDENCE → Escalated | 165 |
| PAYMENT_NOT_COMPLETED (link not paid) | 59 |

## Known Limitations

- This evaluation uses a **synthetic dataset** (not real Razorpay transactions).
- Razorpay API calls were **mocked** to avoid test-mode rate limits.
- The 60% payment success rate is a simulation — real rates vary by customer segment.
- Manual charge (MANUAL_CHARGE) action is excluded from this batch.
- Subscription reactivation rate is not measured separately (requires live webhooks).
