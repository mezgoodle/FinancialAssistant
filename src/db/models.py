import hashlib
from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class TransactionCreate(BaseModel):
    transaction_date: datetime = Field(..., description="Timestamp of the transaction")
    amount: float = Field(..., description="Amount (negative for expenses, positive for income)")
    currency: str = Field(default="UAH", description="Currency code (e.g. UAH, USD, EUR)")
    category: str = Field(default="Інше", description="Category of expense or income")
    description: Optional[str] = Field(default=None, description="Note or description")
    source: str = Field(default="generic", description="Source provider: monobank, privatbank, money_manager, generic")
    dedup_hash: Optional[str] = Field(default=None, description="SHA-256 hash for deduplication")

    @field_validator("currency", mode="before")
    @classmethod
    def normalize_currency(cls, v: Optional[str]) -> str:
        if not v or str(v).strip() == "":
            return "UAH"
        return str(v).strip().upper()

    @field_validator("category", mode="before")
    @classmethod
    def normalize_category(cls, v: Optional[str]) -> str:
        if not v or str(v).strip() == "":
            return "Інше"
        return str(v).strip()

    def compute_hash(self) -> str:
        """Compute deterministic SHA-256 hash for deduplication."""
        # Format date consistently to seconds
        dt_str = self.transaction_date.strftime("%Y-%m-%d %H:%M:%S")
        amt_str = f"{self.amount:.2f}"
        desc_str = (self.description or "").strip().lower()
        cat_str = self.category.strip().lower()
        source_str = self.source.strip().lower()

        raw_str = f"{dt_str}|{amt_str}|{self.currency}|{cat_str}|{desc_str}|{source_str}"
        return hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

    def model_post_init(self, __context):
        if not self.dedup_hash:
            self.dedup_hash = self.compute_hash()


class PeriodSummary(BaseModel):
    start_date: str
    end_date: str
    total_income: float
    total_expense: float
    net_savings: float
    category_breakdown: dict[str, float]
    transaction_count: int


class PeriodComparison(BaseModel):
    period_a: PeriodSummary
    period_b: PeriodSummary
    income_delta: float
    expense_delta: float
    expense_percent_change: Optional[float]
    category_deltas: dict[str, float]
