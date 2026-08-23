from datetime import datetime
from typing import List
import pandas as pd
from dateutil import parser as date_parser

from src.db.models import TransactionCreate


def is_money_manager(df: pd.DataFrame) -> bool:
    cols = [str(c).strip().lower() for c in df.columns]
    # Check for characteristic Money Manager columns
    has_income_expense = any("income/expense" in c or "дохід/витрата" in c or "доход/расход" in c for c in cols)
    has_account = any("account" in c or "рахунок" in c or "счет" in c for c in cols)
    has_category = any("category" in c or "категорія" in c or "категория" in c for c in cols)
    return (has_income_expense or has_account) and has_category


def parse_money_manager(df: pd.DataFrame) -> List[TransactionCreate]:
    transactions: List[TransactionCreate] = []
    
    # Normalize column names mapping
    col_map = {}
    for c in df.columns:
        cl = str(c).strip().lower()
        if "date" in cl or "дата" in cl:
            col_map["date"] = c
        elif "category" in cl or "категорія" in cl or "категория" in cl:
            col_map["category"] = c
        elif "note" in cl or "memo" in cl or "нотатка" in cl or "опис" in cl or "комментарий" in cl:
            col_map["description"] = c
        elif "amount" in cl or "сума" in cl or "сумма" in cl:
            col_map["amount"] = c
        elif "currency" in cl or "валюта" in cl:
            col_map["currency"] = c
        elif "income/expense" in cl or "тип" in cl or "дохід/витрата" in cl or "доход/расход" in cl:
            col_map["type"] = c

    if "date" not in col_map or "amount" not in col_map:
        return []

    for _, row in df.iterrows():
        raw_date = row.get(col_map.get("date"))
        raw_amount = row.get(col_map.get("amount"))

        if pd.isna(raw_date) or pd.isna(raw_amount):
            continue

        # Parse date
        try:
            if isinstance(raw_date, (datetime, pd.Timestamp)):
                dt = raw_date.to_pydatetime() if hasattr(raw_date, "to_pydatetime") else raw_date
            else:
                dt = date_parser.parse(str(raw_date))
        except Exception:
            continue

        # Parse amount
        try:
            amount_val = float(str(raw_amount).replace(" ", "").replace(",", "."))
        except Exception:
            continue

        # Check Income/Expense type
        is_expense = True
        if "type" in col_map and not pd.isna(row.get(col_map["type"])):
            t_str = str(row[col_map["type"]]).strip().lower()
            if "income" in t_str or "дохід" in t_str or "доход" in t_str or "надходження" in t_str:
                is_expense = False
            elif "transfer" in t_str or "переказ" in t_str:
                continue

        if is_expense and amount_val > 0:
            amount_val = -amount_val
        elif not is_expense and amount_val < 0:
            amount_val = abs(amount_val)

        category = str(row.get(col_map.get("category", ""), "Інше")).strip()
        if not category or category.lower() == "nan":
            category = "Інше"

        description = str(row.get(col_map.get("description", ""), "")).strip()
        if not description or description.lower() == "nan":
            description = None

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
                source="money_manager",
            )
        )

    return transactions
