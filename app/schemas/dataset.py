
from typing import Literal

from pydantic import BaseModel


class NumericStatistics(BaseModel):
    mean: float | None = None
    min: float | None = None
    max: float | None = None


class ColumnProfile(BaseModel):
    name: str
    data_type: str
    missing_values: int
    unique_values: int
    numeric_statistics: NumericStatistics | None = None


class DataQualityIssue(BaseModel):
    code: str
    severity: Literal["warning", "error"]
    message: str
    column: str | None = None
    affected_rows: int = 0


class DatasetProfile(BaseModel):
    filename: str
    row_count: int
    column_count: int
    duplicate_rows: int
    columns: list[ColumnProfile]
    quality_issues: list[DataQualityIssue] = []
