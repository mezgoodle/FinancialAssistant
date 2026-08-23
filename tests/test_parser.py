from datetime import datetime
import io
import pandas as pd
from src.parser.engine import parse_financial_file
from src.db.models import TransactionCreate


def test_dedup_hash_stability():
    t1 = TransactionCreate(
        transaction_date=datetime(2026, 8, 1, 14, 30, 0),
        amount=-250.50,
        currency="UAH",
        category="Продукти",
        description="Сільпо",
        source="monobank",
    )
    t2 = TransactionCreate(
        transaction_date=datetime(2026, 8, 1, 14, 30, 0),
        amount=-250.50,
        currency="UAH",
        category="Продукти",
        description="Сільпо",
        source="monobank",
    )
    assert t1.dedup_hash == t2.dedup_hash
    assert len(t1.dedup_hash) == 64


def test_parse_money_manager_csv():
    csv_data = """Date,Account,Category,Amount,Currency,Note,Income/Expense
2026-07-15,Card,Food,350.00,UAH,Dinner,Expense
2026-07-20,Cash,Salary,25000.00,UAH,Monthly bonus,Income
"""
    records, fmt = parse_financial_file(csv_data.encode("utf-8"), filename="export.csv")
    assert fmt == "money_manager"
    assert len(records) == 2
    assert records[0].amount == -350.00
    assert records[0].category == "Food"
    assert records[1].amount == 25000.00
    assert records[1].category == "Salary"


def test_parse_monobank_csv():
    csv_data = """Дата і час,Опис,MCC,Сума,Валюта,Кешбек,Залишок
05.08.2026 12:00,АТБ-Маркет,5411,-180.50,UAH,0.00,15400.00
10.08.2026 18:30,Зарахування зарплати,0000,30000.00,UAH,0.00,45400.00
"""
    records, fmt = parse_financial_file(csv_data.encode("utf-8"), filename="monobank.csv")
    assert fmt == "monobank"
    assert len(records) == 2
    assert records[0].amount == -180.50
    assert records[0].description == "АТБ-Маркет"
    assert records[1].amount == 30000.00


def test_parse_privatbank_csv():
    csv_data = """Дата,Час,Категорія,Картка,Опис операції,Сума,Валюта
01.08.2026,10:15,Кафе та ресторани,5168,Кав'ярня,-65.00,UAH
02.08.2026,14:20,Поповнення,5168,Переказ на картку,1000.00,UAH
"""
    records, fmt = parse_financial_file(csv_data.encode("utf-8"), filename="privat.csv")
    assert fmt == "privatbank"
    assert len(records) == 2
    assert records[0].amount == -65.00
    assert records[0].category == "Кафе та ресторани"
