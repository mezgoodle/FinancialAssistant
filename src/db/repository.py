from datetime import datetime, date
from typing import List, Optional, Dict, Any
from dateutil import parser as date_parser

from src.db.client import get_supabase_client
from src.db.models import TransactionCreate, PeriodSummary, PeriodComparison


class TransactionRepository:
    """Handles persistence, batch upserting, deduplication and analytical queries."""

    def __init__(self):
        self._in_memory_db: Dict[str, dict] = {}

    def upsert_transactions(self, records: List[TransactionCreate]) -> Dict[str, int]:
        """
        Inserts transactions while skipping duplicates based on dedup_hash.
        Returns counts of total, inserted, and skipped records.
        """
        if not records:
            return {"total": 0, "inserted": 0, "skipped": 0}

        supabase = get_supabase_client()
        total = len(records)
        inserted = 0

        if supabase:
            # Batch upsert via Supabase PostgreSQL
            payload = []
            for r in records:
                payload.append({
                    "transaction_date": r.transaction_date.isoformat(),
                    "amount": r.amount,
                    "currency": r.currency,
                    "category": r.category,
                    "description": r.description,
                    "source": r.source,
                    "dedup_hash": r.dedup_hash,
                })
            
            try:
                # Upsert with ignore_duplicates=True
                response = supabase.table("transactions").upsert(
                    payload,
                    on_conflict="dedup_hash",
                    ignore_duplicates=True,
                ).execute()
                inserted = len(response.data) if response.data else 0
            except Exception as e:
                print(f"Supabase upsert error: {e}. Falling back to in-memory store.")
                supabase = None

        if not supabase:
            # In-memory storage with hash deduplication
            for r in records:
                if r.dedup_hash not in self._in_memory_db:
                    self._in_memory_db[r.dedup_hash] = {
                        "transaction_date": r.transaction_date.isoformat(),
                        "amount": r.amount,
                        "currency": r.currency,
                        "category": r.category,
                        "description": r.description,
                        "source": r.source,
                        "dedup_hash": r.dedup_hash,
                    }
                    inserted += 1

        skipped = total - inserted
        return {"total": total, "inserted": inserted, "skipped": skipped}

    def _get_all_records(self) -> List[dict]:
        supabase = get_supabase_client()
        if supabase:
            try:
                res = supabase.table("transactions").select("*").execute()
                if res.data:
                    return res.data
            except Exception:
                pass
        return list(self._in_memory_db.values())

    def query_transactions(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        keyword: Optional[str] = None,
        limit: int = 50,
    ) -> List[dict]:
        """Query transactions matching specific criteria."""
        records = self._get_all_records()
        filtered = []

        start_dt = date_parser.parse(start_date) if start_date else None
        end_dt = date_parser.parse(end_date) if end_date else None
        if end_dt and len(end_date) <= 10:
            # Include entire end day
            end_dt = end_dt.replace(hour=23, minute=59, second=59)

        for r in records:
            r_dt = date_parser.parse(r["transaction_date"])
            if start_dt and r_dt < start_dt:
                continue
            if end_dt and r_dt > end_dt:
                continue
            if category and category.lower() not in r["category"].lower():
                continue
            if min_amount is not None and r["amount"] < min_amount:
                continue
            if max_amount is not None and r["amount"] > max_amount:
                continue
            if keyword:
                kw = keyword.lower()
                desc = (r.get("description") or "").lower()
                cat = r["category"].lower()
                if kw not in desc and kw not in cat:
                    continue
            filtered.append(r)

        # Sort by transaction_date descending
        filtered.sort(key=lambda x: x["transaction_date"], reverse=True)
        return filtered[:limit]

    def get_period_summary(self, start_date: str, end_date: str) -> PeriodSummary:
        """Calculate aggregated spending, income and category breakdown for a period."""
        records = self.query_transactions(start_date=start_date, end_date=end_date, limit=10000)
        
        total_income = 0.0
        total_expense = 0.0
        cat_breakdown: Dict[str, float] = {}

        for r in records:
            amt = float(r["amount"])
            cat = r.get("category", "Інше")
            if amt > 0:
                total_income += amt
            else:
                exp_amt = abs(amt)
                total_expense += exp_amt
                cat_breakdown[cat] = cat_breakdown.get(cat, 0.0) + exp_amt

        # Sort categories by highest expense
        sorted_cats = dict(sorted(cat_breakdown.items(), key=lambda item: item[1], reverse=True))

        return PeriodSummary(
            start_date=start_date,
            end_date=end_date,
            total_income=round(total_income, 2),
            total_expense=round(total_expense, 2),
            net_savings=round(total_income - total_expense, 2),
            category_breakdown={k: round(v, 2) for k, v in sorted_cats.items()},
            transaction_count=len(records),
        )

    def compare_periods(
        self,
        period_a_start: str,
        period_a_end: str,
        period_b_start: str,
        period_b_end: str,
    ) -> PeriodComparison:
        """
        Compare period A (e.g. current month) with period B (e.g. previous month or year ago).
        """
        summary_a = self.get_period_summary(period_a_start, period_a_end)
        summary_b = self.get_period_summary(period_b_start, period_b_end)

        income_delta = round(summary_a.total_income - summary_b.total_income, 2)
        expense_delta = round(summary_a.total_expense - summary_b.total_expense, 2)

        percent_change = None
        if summary_b.total_expense > 0:
            percent_change = round((expense_delta / summary_b.total_expense) * 100.0, 1)

        # Calculate category differences
        all_categories = set(summary_a.category_breakdown.keys()).union(set(summary_b.category_breakdown.keys()))
        category_deltas = {}
        for c in all_categories:
            val_a = summary_a.category_breakdown.get(c, 0.0)
            val_b = summary_b.category_breakdown.get(c, 0.0)
            category_deltas[c] = round(val_a - val_b, 2)

        sorted_category_deltas = dict(sorted(category_deltas.items(), key=lambda item: abs(item[1]), reverse=True))

        return PeriodComparison(
            period_a=summary_a,
            period_b=summary_b,
            income_delta=income_delta,
            expense_delta=expense_delta,
            expense_percent_change=percent_change,
            category_deltas=sorted_category_deltas,
        )
