from typing import Optional, Dict, Any, List
from pathlib import Path

from src.parser.engine import parse_financial_file
from src.db.repository import TransactionRepository

# Global repository instance
_repo = TransactionRepository()


def get_repository() -> TransactionRepository:
    return _repo


def set_repository(repo: TransactionRepository) -> None:
    global _repo
    _repo = repo


def reset_repository() -> None:
    global _repo
    _repo = TransactionRepository()


def ingest_financial_file(file_path: str, format_hint: Optional[str] = None) -> Dict[str, Any]:
    """
    Імпортує та парсить банківський файл виписки (CSV або Excel .xlsx) у базу даних.
    Підтримує Money Manager, Monobank, ПриватБанк та стандартні CSV.

    Args:
        file_path: Шлях до завантаженого файлу (наприклад: 'data/uploads/statement.csv').
        format_hint: Опціональна підказка формату ('monobank', 'privatbank', 'money_manager').

    Returns:
        Словник із результатами імпорту: кількість розпарсених, доданих та пропущених дублікатів.
    """
    path = Path(file_path)
    if not path.exists():
        return {"error": f"Файл за шляхом '{file_path}' не знайдено."}

    try:
        transactions, detected_format = parse_financial_file(path, filename=path.name, format_hint=format_hint)
        if not transactions:
            return {
                "success": False,
                "message": f"Не вдалося знайти валідні транзакції у файлі '{path.name}'. Перевірте формат.",
            }

        repo = get_repository()
        stats = repo.upsert_transactions(transactions)

        return {
            "success": True,
            "filename": path.name,
            "detected_format": detected_format,
            "total_parsed": stats["total"],
            "inserted_new": stats["inserted"],
            "duplicates_skipped": stats["skipped"],
            "message": f"Успішно імпортовано {stats['inserted']} нових транзакцій (пропущено дублікатів: {stats['skipped']}). Формат: {detected_format}.",
        }
    except Exception as e:
        return {"success": False, "error": f"Помилка парсингу файлу: {str(e)}"}


def query_transactions(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    category: Optional[str] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    keyword: Optional[str] = None,
    limit: int = 30,
) -> List[Dict[str, Any]]:
    """
    Шукає та фільтрує детальні транзакції користувача за критеріями.

    Args:
        start_date: Початкова дата у форматі 'YYYY-MM-DD' (наприклад: '2026-08-01').
        end_date: Кінцева дата у форматі 'YYYY-MM-DD' (наприклад: '2026-08-31').
        category: Назва категорії витрат (наприклад: 'Продукти', 'Кафе', 'Транспорт').
        min_amount: Мінімальна сума транзакції (від'ємна для витрат, наприклад -500.0).
        max_amount: Максимальна сума транзакції.
        keyword: Ключове слово для пошуку в описі або категорії (наприклад: 'Сільпо', 'Uber').
        limit: Максимальна кількість результатів (за замовчуванням 30).

    Returns:
        Список знайдених транзакцій із датою, сумою, категорією та описом.
    """
    repo = get_repository()
    return repo.query_transactions(
        start_date=start_date,
        end_date=end_date,
        category=category,
        min_amount=min_amount,
        max_amount=max_amount,
        keyword=keyword,
        limit=limit,
    )


def get_period_summary(start_date: str, end_date: str) -> Dict[str, Any]:
    """
    Розраховує зведену фінансову статистику за вказаний період часу.

    Args:
        start_date: Початкова дата у форматі 'YYYY-MM-DD' (наприклад: '2026-08-01').
        end_date: Кінцева дата у форматі 'YYYY-MM-DD' (наприклад: '2026-08-31').

    Returns:
        Словник із загальним доходом, загальними витратами, чистим залишком та розбивкою по категоріях.
    """
    repo = get_repository()
    summary = repo.get_period_summary(start_date, end_date)
    return summary.model_dump()


def compare_periods(
    period_a_start: str,
    period_a_end: str,
    period_b_start: str,
    period_b_end: str,
) -> Dict[str, Any]:
    """
    Порівнює фінансові показники між двома періодами (наприклад: поточний місяць проти минулого місяця, або серпень 2026 проти серпня 2025).

    Args:
        period_a_start: Початок першого (основного/поточного) періоду 'YYYY-MM-DD'.
        period_a_end: Кінець першого періоду 'YYYY-MM-DD'.
        period_b_start: Початок другого (минулого/порівнювального) періоду 'YYYY-MM-DD'.
        period_b_end: Кінець другого періоду 'YYYY-MM-DD'.

    Returns:
        Словник із дельтою витрат, дельтою доходів, зміною у відсотках та зміною по окремих категоріях.
    """
    repo = get_repository()
    comp = repo.compare_periods(
        period_a_start=period_a_start,
        period_a_end=period_a_end,
        period_b_start=period_b_start,
        period_b_end=period_b_end,
    )
    return comp.model_dump()


ALL_TOOLS = [
    ingest_financial_file,
    query_transactions,
    get_period_summary,
    compare_periods,
]
