from typing import Literal

from pydantic import BaseModel


TrendPeriod = Literal["day", "week", "month"]


class SalesTrendPoint(BaseModel):
    period_start: str
    revenue: float
    units_sold: int
    revenue_growth_percent: float | None = None


class SalesTrend(BaseModel):
    period: TrendPeriod
    row_count: int
    total_units_sold: int
    total_revenue: float
    trend: list[SalesTrendPoint]