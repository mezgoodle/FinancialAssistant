import io
from pathlib import Path
from src.agent.tools import (
    ingest_financial_file,
    query_transactions,
    get_period_summary,
    compare_periods,
    get_repository,
)


def test_tools_end_to_end_flow(tmp_path: Path):
    csv_content = """Date,Account,Category,Amount,Currency,Note,Income/Expense
2026-08-01,Card,Продукти,600.00,UAH,Сільпо,Expense
2026-08-05,Card,Кафе,150.00,UAH,Кава,Expense
2026-08-10,Card,Зарплата,25000.00,UAH,Аванс,Income
2026-07-01,Card,Продукти,450.00,UAH,АТБ,Expense
2026-07-05,Card,Кафе,120.00,UAH,Кава,Expense
2025-08-01,Card,Продукти,400.00,UAH,Сільпо,Expense
"""
    test_file = tmp_path / "test_statement.csv"
    test_file.write_text(csv_content, encoding="utf-8")

    # 1. Ingest
    res = ingest_financial_file(str(test_file))
    assert res["success"] is True
    assert res["total_parsed"] == 6

    # 2. Query transactions
    txs = query_transactions(start_date="2026-08-01", end_date="2026-08-31", category="Продукти")
    assert len(txs) == 1
    assert txs[0]["amount"] == -600.00

    # 3. Period summary
    summary = get_period_summary(start_date="2026-08-01", end_date="2026-08-31")
    assert summary["total_income"] == 25000.00
    assert summary["total_expense"] == 750.00
    assert summary["category_breakdown"]["Продукти"] == 600.00
    assert summary["category_breakdown"]["Кафе"] == 150.00

    # 4. Month-over-Month comparison (August 2026 vs July 2026)
    mom_comp = compare_periods(
        period_a_start="2026-08-01",
        period_a_end="2026-08-31",
        period_b_start="2026-07-01",
        period_b_end="2026-07-31",
    )
    # August expenses = 750, July expenses = 570 (diff +180)
    assert mom_comp["expense_delta"] == 180.00
    assert mom_comp["category_deltas"]["Продукти"] == 150.00
    assert mom_comp["category_deltas"]["Кафе"] == 30.00

    # 5. Year-over-Year comparison (August 2026 vs August 2025)
    yoy_comp = compare_periods(
        period_a_start="2026-08-01",
        period_a_end="2026-08-31",
        period_b_start="2025-08-01",
        period_b_end="2025-08-31",
    )
    # August 2026 expenses = 750, August 2025 expenses = 400 (diff +350)
    assert yoy_comp["expense_delta"] == 350.00
    assert yoy_comp["category_deltas"]["Продукти"] == 200.00
