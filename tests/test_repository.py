from datetime import datetime
from src.db.models import TransactionCreate
from src.db.repository import TransactionRepository


def test_repository_upsert_and_dedup():
    repo = TransactionRepository()

    t1 = TransactionCreate(
        transaction_date=datetime(2026, 8, 1, 10, 0),
        amount=-100.0,
        category="Транспорт",
        description="Метро",
        source="generic",
    )
    t2 = TransactionCreate(
        transaction_date=datetime(2026, 8, 1, 10, 0),
        amount=-100.0,
        category="Транспорт",
        description="Метро",
        source="generic",
    )
    t3 = TransactionCreate(
        transaction_date=datetime(2026, 8, 2, 11, 0),
        amount=-200.0,
        category="Продукти",
        description="Сільпо",
        source="generic",
    )

    res1 = repo.upsert_transactions([t1, t2])
    assert res1["total"] == 2
    assert res1["inserted"] == 1
    assert res1["skipped"] == 1

    # Upload same t1 again with new t3
    res2 = repo.upsert_transactions([t1, t3])
    assert res2["total"] == 2
    assert res2["inserted"] == 1
    assert res2["skipped"] == 1


def test_repository_period_summary_and_compare():
    repo = TransactionRepository()

    # Month A (August 2026)
    repo.upsert_transactions([
        TransactionCreate(
            transaction_date=datetime(2026, 8, 5),
            amount=-500.0,
            category="Продукти",
            description="Супермаркет",
        ),
        TransactionCreate(
            transaction_date=datetime(2026, 8, 10),
            amount=-200.0,
            category="Кафе",
            description="Кава",
        ),
        TransactionCreate(
            transaction_date=datetime(2026, 8, 1),
            amount=20000.0,
            category="Зарплата",
            description="Основна",
        ),
    ])

    # Month B (July 2026)
    repo.upsert_transactions([
        TransactionCreate(
            transaction_date=datetime(2026, 7, 5),
            amount=-400.0,
            category="Продукти",
            description="Супермаркет",
        ),
        TransactionCreate(
            transaction_date=datetime(2026, 7, 10),
            amount=-100.0,
            category="Кафе",
            description="Кава",
        ),
        TransactionCreate(
            transaction_date=datetime(2026, 7, 1),
            amount=20000.0,
            category="Зарплата",
            description="Основна",
        ),
    ])

    summary_aug = repo.get_period_summary("2026-08-01", "2026-08-31")
    assert summary_aug.total_income == 20000.0
    assert summary_aug.total_expense == 700.0
    assert summary_aug.category_breakdown["Продукти"] == 500.0
    assert summary_aug.category_breakdown["Кафе"] == 200.0

    comparison = repo.compare_periods(
        period_a_start="2026-08-01",
        period_a_end="2026-08-31",
        period_b_start="2026-07-01",
        period_b_end="2026-07-31",
    )
    # Total expenses increased from 500 to 700 (+200)
    assert comparison.expense_delta == 200.0
    assert comparison.expense_percent_change == 40.0
    assert comparison.category_deltas["Продукти"] == 100.0
    assert comparison.category_deltas["Кафе"] == 100.0
