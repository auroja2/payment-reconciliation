# Payment Reconciliation System

## Structure
```
backend/
  main.py          — FastAPI app (routes: /generate, /reconcile, /report, /transactions)
  generator.py     — Synthetic dataset generator with anomalies
  reconciler.py    — Outer-join + rule-based reconciliation engine
  test_reconcile.py — 10 pytest tests
  requirements.txt
```

## Setup & Run

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --port 8765 --reload
```

## API

| Method | Path | Description |
|--------|------|-------------|
| POST | /generate | Generate datasets (body: `{"num_txns": 40}`) |
| POST | /reconcile | Run reconciliation on current data |
| GET  | /report | Fetch latest reconciliation report |
| GET  | /transactions | View raw platform + bank data |
| GET  | /health | Health check |

## Anomaly Types Generated
- Missing in bank / Extra in bank
- Delayed settlement (28-35 days)
- Duplicate bank entries
- Rounding differences (within ₹2)
- Amount mismatches / FX mismatch (INR↔USD at 83.5)
- Refunds (platform REFUND ↔ bank DEBIT)

## Reconciliation Rules
| Status | Rule |
|--------|------|
| MATCHED | Exact INR-normalized amount match |
| MISSING_IN_BANK | Present on platform, absent in bank |
| EXTRA_IN_BANK | Present in bank, absent on platform |
| DUPLICATE_IN_BANK | Same txn_id appears 2+ times in bank |
| DELAYED_MONTH | Date gap ≥ 28 days between platform and bank |
| ROUNDING_DIFF | Amount diff ≤ ₹2 |
| AMOUNT_MISMATCH | Amount diff > ₹2 (incl. FX mismatch) |
| REFUND_MATCHED | Platform REFUND ↔ bank DEBIT |
| UNMATCHED_REFUND | Refund not matched as debit |

## Tests
```bash
cd backend && pytest test_reconcile.py -v
```
10 tests, all passing.
