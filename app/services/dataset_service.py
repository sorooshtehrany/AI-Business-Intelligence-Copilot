
import math

import pandas as pd

from app.schemas.dataset import (
    ColumnProfile,
    DataQualityIssue,
    DatasetProfile,
    NumericStatistics,
)


def profile_dataframe(
    dataframe: pd.DataFrame,
    filename: str,
) -> DatasetProfile:
    columns = []
    quality_issues = []

    # Check duplicate rows.
    duplicate_count = int(dataframe.duplicated().sum())

    if duplicate_count > 0:
        quality_issues.append(
            DataQualityIssue(
                code="DUPLICATE_ROWS",
                severity="warning",
                message=f"Found {duplicate_count} duplicate rows.",
                affected_rows=duplicate_count,
            )
        )

    # Analyze each column.
    for column_name in dataframe.columns:
        series = dataframe[column_name]

        missing_count = int(series.isna().sum())
        unique_count = int(series.nunique())

        numeric_statistics = None

        # Detect completely empty columns.
        if len(series) > 0 and missing_count == len(series):
            quality_issues.append(
                DataQualityIssue(
                    code="EMPTY_COLUMN",
                    severity="warning",
                    message="The column contains no non-missing values.",
                    column=str(column_name),
                    affected_rows=len(series),
                )
            )

        # Detect non-finite numeric values.
        if pd.api.types.is_numeric_dtype(series):
            finite_mask = series.map(
                lambda value: (
                    True
                    if pd.isna(value)
                    else math.isfinite(float(value))
                )
            )

            non_finite_count = int((~finite_mask).sum())

            if non_finite_count > 0:
                quality_issues.append(
                    DataQualityIssue(
                        code="NON_FINITE_VALUES",
                        severity="warning",
                        message=(
                            "The column contains infinite numeric values."
                        ),
                        column=str(column_name),
                        affected_rows=non_finite_count,
                    )
                )

            # Exclude missing and non-finite values from statistics.
            values = series[finite_mask].dropna()

            if len(values) > 0:
                mean_value = float(values.mean())
                min_value = float(values.min())
                max_value = float(values.max())

                numeric_statistics = NumericStatistics(
                    mean=(
                        mean_value
                        if math.isfinite(mean_value)
                        else None
                    ),
                    min=(
                        min_value
                        if math.isfinite(min_value)
                        else None
                    ),
                    max=(
                        max_value
                        if math.isfinite(max_value)
                        else None
                    ),
                )

        columns.append(
            ColumnProfile(
                name=str(column_name),
                data_type=str(series.dtype),
                missing_values=missing_count,
                unique_values=unique_count,
                numeric_statistics=numeric_statistics,
            )
        )

    return DatasetProfile(
        filename=filename,
        row_count=len(dataframe),
        column_count=len(dataframe.columns),
        duplicate_rows=duplicate_count,
        columns=columns,
        quality_issues=quality_issues,
    )
