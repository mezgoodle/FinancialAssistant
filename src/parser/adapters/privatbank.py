from datetime import datetime
from typing import List
import pandas as pd
from dateutil import parser as date_parser

from src.db.models import TransactionCreate


def is_privatbank(df: pd.DataFrame) -> bool:
    cols = [str(c).strip().lower() for c in df.columns]
    has_card = any("картка" in c or "карта" in c or "card" in c for c in cols)
    has_operation = any("операція" in c or "операция" in c or "детали операции" in c for c in cols)
    return has_card or has_operation


def parse_privatbank(df: pd.DataFrame) -> List[TransactionCreate]:
    transactions: List[TransactionCreate] = []

    col_map = {}
    for c in df.columns:
        cl = str(c).strip().lower()
        if "дата" in cl or "date" in cl:
            col_map["date"] = c
        elif "час" in cl or "time" in cl:
            col_map["time"] = c
        elif "опис" in cl or "операція" in cl or "детали" in cl or "description" in cl:
            col_map["description"] = c
        elif "категорія" in cl or "category" in cl:
            col_map["category"] = c
        elif "сума" in cl or "amount" in cl:
            if "сума в валюті" not in cl and "залишок" not in cl:
                col_map["amount"] = c
        elif "валюта" in cl or "currency" in cl:
            col_map["currency"] = c

    if "date" not in col_map or "amount" not in col_map:
        return []

    for _, row in df.iterrows():
        raw_date = row.get(col_map.get("date"))
        raw_time = row.get(col_map.get("time"))
        raw_amount = row.get(col_map.get("amount"))

        if pd.isna(raw_date) or pd.isna(raw_amount):
            continue

        date_str = str(raw_date)
        if raw_time and not pd.isna(raw_time):
            date_str += f" {str(raw_time)}"

        try:
            if isinstance(raw_date, (datetime, pd.Timestamp)) and pd.isna(raw_time):
                dt = raw_date.to_pydatetime() if hasattr(raw_date, "to_pydatetime") else raw_date
            else:
                dt = date_parser.parse(date_str, dayfirst=True)
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
                source="privatbank",
            )
        )

    return transactions
