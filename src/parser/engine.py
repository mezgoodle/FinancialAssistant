import io
from pathlib import Path
from typing import List, Union
import pandas as pd

from src.db.models import TransactionCreate
from src.parser.adapters.money_manager import is_money_manager, parse_money_manager
from src.parser.adapters.monobank import is_monobank, parse_monobank
from src.parser.adapters.privatbank import is_privatbank, parse_privatbank


def read_dataframe(file_source: Union[str, Path, bytes, io.BytesIO], filename: str = "") -> pd.DataFrame:
    """Read CSV or Excel file into a Pandas DataFrame with automatic delimiter sniffing."""
    if isinstance(file_source, (str, Path)):
        p = Path(file_source)
        filename = filename or p.name
        if p.suffix.lower() in [".xlsx", ".xls"]:
            return pd.read_excel(p)
        
        # Try CSV with different separators
        for sep in [",", ";", "\t"]:
            try:
                df = pd.read_csv(p, sep=sep)
                if len(df.columns) > 1:
                    return df
            except Exception:
                continue
        return pd.read_csv(p)

    # In-memory Bytes
    if isinstance(file_source, bytes):
        buffer = io.BytesIO(file_source)
    else:
        buffer = file_source

    if filename.endswith(".xlsx") or filename.endswith(".xls"):
        return pd.read_excel(buffer)

    # For CSV in-memory
    content = buffer.getvalue()
    for sep in [",", ";", "\t"]:
        try:
            df = pd.read_csv(io.BytesIO(content), sep=sep)
            if len(df.columns) > 1:
                return df
        except Exception:
            continue
    return pd.read_csv(io.BytesIO(content))


def parse_generic(df: pd.DataFrame) -> List[TransactionCreate]:
    """Fallback generic parser using standard column name heuristics."""
    # Attempt money manager parser as generic fallback
    return parse_money_manager(df)


def parse_financial_file(
    file_source: Union[str, Path, bytes, io.BytesIO],
    filename: str = "",
    format_hint: str = None,
) -> tuple[List[TransactionCreate], str]:
    """
    Parses a financial file (CSV or Excel) and returns a list of validated TransactionCreate objects
    and the detected format name.
    """
    df = read_dataframe(file_source, filename)
    df = df.dropna(how="all")

    if format_hint:
        f_lower = format_hint.lower()
        if "mono" in f_lower:
            return parse_monobank(df), "monobank"
        if "privat" in f_lower:
            return parse_privatbank(df), "privatbank"
        if "money" in f_lower:
            return parse_money_manager(df), "money_manager"

    # Auto-detection
    if is_monobank(df):
        return parse_monobank(df), "monobank"
    elif is_privatbank(df):
        return parse_privatbank(df), "privatbank"
    elif is_money_manager(df):
        return parse_money_manager(df), "money_manager"
    else:
        # Fallback to generic
        return parse_generic(df), "generic"
