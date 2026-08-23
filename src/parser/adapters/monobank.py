from datetime import datetime
from typing import List
import pandas as pd
from dateutil import parser as date_parser

from src.db.models import TransactionCreate


def is_monobank(df: pd.DataFrame) -> bool:
    cols = [str(c).strip().lower() for c in df.columns]
    has_mcc = any("mcc" in c for c in cols)
    has_cashback = any("кешбек" in c or "cashback" in c for c in cols)
    has_balance = any("залишок" in c or "баланс" in c or "balance" in c for c in cols)
    return has_mcc or (has_cashback and has_balance)


def parse_monobank(df: pd.DataFrame) -> List[TransactionCreate]:
    transactions: List[TransactionCreate] = []

    col_map = {}
    for c in df.columns:
        cl = str(c).strip().lower()
        if "дата" in cl or "date" in cl or "час" in cl or "time" in cl:
            col_map["date"] = c
        elif "опис" in cl or "деталі" in cl or "description" in cl:
            col_map["description"] = c
        elif "сума" in cl or "amount" in cl:
            # Avoid picking fee or cashback as main amount
            if "сума в валюті" not in cl and "кешбек" not in cl and "комісія" not in cl:
                col_map["amount"] = c
        elif "категорія" in cl or "category" in cl or "mcc" in cl:
            col_map["category"] = c
        elif "валюта" in cl or "currency" in cl:
            col_map["currency"] = c

    if "date" not in col_map or "amount" not in col_map:
        return []

    for _, row in df.iterrows():
        raw_date = row.get(col_map.get("date"))
        raw_amount = row.get(col_map.get("amount"))

        if pd.isna(raw_date) or pd.isna(raw_amount):
            continue

        try:
            if isinstance(raw_date, (datetime, pd.Timestamp)):
                dt = raw_date.to_pydatetime() if hasattr(raw_date, "to_pydatetime") else raw_date
            else:
                dt = date_parser.parse(str(raw_date), dayfirst=True)
        except Exception:
            continue

        try:
            amount_val = float(str(raw_amount).replace(" ", "").replace(",", "."))
        except Exception:
            continue

        description = str(row.get(col_map.get("description", ""), "")).strip()
        if not description or description.lower() == "nan":
            description = None

        category = str(row.get(col_map.get("category", ""), "Інше")).strip()
        if not category or category.lower() == "nan":
            category = "Інше"

        currency = str(row.get(col_map.get("currency", "UAH"), "UAH")).strip()
        if not currency or currency.lower() == "nan":
            currency = "UAH"

        transactions.append(
            TransactionCreate(
                transaction_date=dt,
                amount=amount_val,
                currency=currency,
                category=category,
                description=description,
                source="monobank",
            )
        )

    return transactions
