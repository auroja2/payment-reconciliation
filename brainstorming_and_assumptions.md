# Brainstorming Thread & Assumptions

## Problem Understanding

- The payments company needs to reconcile its internal transaction records with the bank's settlement records at month end.
- Every platform transaction should have a matching bank settlement, but mismatches (gaps) can occur.

## Assumptions

- Platform records transactions instantly; bank settles in batches 1-2 days later.
- Data is available as CSV or similar tabular format.
- Gaps to plant:
  - Settlement in next month
  - Rounding difference (shows only when summed)
  - Duplicate entry in one dataset
  - Refund with no matching original transaction
- Each transaction has a unique ID, date, and amount.
- Refunds are negative amounts.

## Approach

- Generate synthetic test data for both platform and bank.
- Implement reconciliation logic to:
  - Match transactions by ID and amount (allowing for settlement delay)
  - Identify and report gaps (missing, duplicate, rounding, refund issues)
- Build a simple web UI for upload/display, make it professional.
- Write test cases for all gap types.

---

## Design Decisions

- Use Python for backend, JS/HTML/CSS for frontend.
- Use pandas for data handling.
- UI: Clean, modern, responsive.
- Output: Table of gaps, downloadable report.
