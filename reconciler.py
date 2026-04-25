"""Reconciliation engine: outer-join + rule-based classification."""
from __future__ import annotations

from typing import Any
import pandas as pd

USD_TO_INR = 83.5
ROUNDING_TOLERANCE = 2.0  # INR


def _to_inr(row: pd.Series) -> float:
    if row["currency"] == "USD":
        return round(row["amount"] * USD_TO_INR, 2)
    return row["amount"]


def reconcile(platform: list[dict], bank: list[dict]) -> dict[str, Any]:
    _cols = ["txn_id", "amount", "currency", "date", "type"]
    p = pd.DataFrame(platform, columns=_cols) if platform else pd.DataFrame(columns=_cols)
    b = pd.DataFrame(bank, columns=_cols) if bank else pd.DataFrame(columns=_cols)

    # normalize to INR
    p["amount_inr"] = p.apply(_to_inr, axis=1) if not p.empty else pd.Series(dtype=float)
    b["amount_inr"] = b.apply(_to_inr, axis=1) if not b.empty else pd.Series(dtype=float)

    # detect bank duplicates before join
    dup_mask = b.duplicated(subset=["txn_id", "amount_inr"], keep=False)
    dup_ids = set(b[dup_mask]["txn_id"])

    # outer join on txn_id (keep first occurrence for duplicates)
    b_dedup = b.drop_duplicates(subset=["txn_id", "amount_inr"])
    merged = pd.merge(
        p.rename(columns={"amount": "p_amount", "amount_inr": "p_inr",
                          "currency": "p_cur", "date": "p_date", "type": "p_type"}),
        b_dedup.rename(columns={"amount": "b_amount", "amount_inr": "b_inr",
                                "currency": "b_cur", "date": "b_date", "type": "b_type"}),
        on="txn_id",
        how="outer",
        indicator=True,
    )

    results: list[dict] = []

    for _, row in merged.iterrows():
        tid = row["txn_id"]
        status, notes = _classify(row, dup_ids)
        
        # Get original amounts before INR conversion
        p_orig_amount = _safe(row, "p_amount")
        b_orig_amount = _safe(row, "b_amount")
        p_cur = _safe(row, "p_cur")
        b_cur = _safe(row, "b_cur")
        
        # Check if this is a currency conversion case
        is_currency_conversion = p_cur == "USD" and b_cur == "INR"
        
        results.append({
            "txn_id": tid,
            "status": status,
            "notes": notes,
            "platform_amount": _safe(row, "p_inr"),
            "bank_amount": _safe(row, "b_inr"),
            "platform_original_amount": p_orig_amount,
            "bank_original_amount": b_orig_amount,
            "platform_date": _safe(row, "p_date"),
            "bank_date": _safe(row, "b_date"),
            "platform_currency": p_cur,
            "bank_currency": b_cur,
            "platform_type": _safe(row, "p_type"),
            "bank_type": _safe(row, "b_type"),
            "is_currency_conversion": is_currency_conversion,
        })

    # summary
    from collections import Counter
    counts = Counter(r["status"] for r in results)
    total = len(results)
    matched = counts.get("MATCHED", 0)
    
    # Count currency conversions
    currency_conversions = sum(1 for r in results if r.get("is_currency_conversion"))

    return {
        "results": results,
        "summary": {
            "total": total,
            "matched": matched,
            "match_rate": round(matched / total * 100, 1) if total else 0,
            "currency_conversions": currency_conversions,
            **{k: v for k, v in counts.items() if k != "MATCHED"},
        },
    }


def _classify(row: pd.Series, dup_ids: set) -> tuple[str, str]:
    tid = row["txn_id"]
    side = row["_merge"]

    if side == "left_only":
        return "MISSING_IN_BANK", "Transaction present on platform but absent in bank"

    if side == "right_only":
        return "EXTRA_IN_BANK", "Transaction present in bank but absent on platform"

    if tid in dup_ids:
        return "DUPLICATE_IN_BANK", "Same txn_id appears multiple times in bank statement"

    p_type = _safe(row, "p_type")
    b_type = _safe(row, "b_type")
    if p_type == "REFUND" and b_type == "DEBIT":
        return "REFUND_MATCHED", "Refund correctly reflected as debit in bank"
    if p_type == "REFUND" and b_type != "DEBIT":
        return "UNMATCHED_REFUND", "Refund on platform not matched as debit in bank"

    p_date = str(_safe(row, "p_date") or "")
    b_date = str(_safe(row, "b_date") or "")
    if p_date and b_date:
        from datetime import datetime
        try:
            d1 = datetime.strptime(p_date, "%Y-%m-%d")
            d2 = datetime.strptime(b_date, "%Y-%m-%d")
            if abs((d2 - d1).days) >= 28:
                return "DELAYED_MONTH", f"Bank settled {abs((d2-d1).days)}d after platform date"
        except ValueError:
            pass

    p_inr = _safe(row, "p_inr") or 0
    b_inr = _safe(row, "b_inr") or 0
    diff = abs(p_inr - b_inr)

    if diff == 0:
        return "MATCHED", "Exact match"
    if diff <= 2.0:
        return "ROUNDING_DIFF", f"Within tolerance (Δ₹{diff:.2f})"
    if diff > 2.0:
        return "AMOUNT_MISMATCH", f"Amount differs by ₹{diff:.2f} (possible FX mismatch)"

    return "MATCHED", "Exact match"


def _safe(row: pd.Series, col: str):
    try:
        v = row[col]
        return None if pd.isna(v) else v
    except (KeyError, TypeError):
        return None
