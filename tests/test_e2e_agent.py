from pathlib import Path
from src.agent.tools import ingest_financial_file, query_transactions, get_period_summary, compare_periods


def test_e2e_multi_year_ingestion_and_comparisons():
    samples_dir = Path("data/samples")
    file_2025 = samples_dir / "sample_money_manager_2025.csv"
    file_2026 = samples_dir / "sample_money_manager_2026.csv"
    file_mono = samples_dir / "sample_monobank_statement.csv"

    # Ingest 2025
    res25 = ingest_financial_file(str(file_2025))
    assert res25["success"] is True
    assert res25["total_parsed"] == 7

    # Ingest 2026
    res26 = ingest_financial_file(str(file_2026))
    assert res26["success"] is True
    assert res26["total_parsed"] == 12

    # Ingest Mono
    res_mono = ingest_financial_file(str(file_mono))
    assert res_mono["success"] is True
    assert res_mono["total_parsed"] == 5

    # Test Year-over-Year (August 2026 vs August 2025)
    yoy = compare_periods(
        period_a_start="2026-08-01",
        period_a_end="2026-08-31",
        period_b_start="2025-08-01",
        period_b_end="2025-08-31",
    )
    assert yoy["period_a"]["total_expense"] > 0
    assert yoy["period_b"]["total_expense"] > 0
    assert "Продукти" in yoy["category_deltas"]

    # Test Month-over-Month (August 2026 vs July 2026)
    mom = compare_periods(
        period_a_start="2026-08-01",
        period_a_end="2026-08-31",
        period_b_start="2026-07-01",
        period_b_end="2026-07-31",
    )
    assert mom["period_a"]["total_income"] > 0
    assert mom["period_b"]["total_income"] > 0

    # Query specific keywords
    silpo_txs = query_transactions(keyword="Сільпо")
    assert len(silpo_txs) >= 3
