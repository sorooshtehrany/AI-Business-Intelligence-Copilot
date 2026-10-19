import math

import pandas as pd

from app.schemas.trends import (
    SalesTrend,
    SalesTrendPoint,
    TrendPeriod,
)

from app.services.calendar_service import load_business_calendar

def calculate_sales_trend(
    dataframe: pd.DataFrame,
    period: TrendPeriod = "day",
    business_calendar: pd.DataFrame | None = None,
    date_column: str = "date",
    quantity_column: str = "quantity",
    unit_price_column: str = "unit_price",
) -> SalesTrend:
    if period not in ("day", "week", "month"):
        raise ValueError("Period must be day, week, or month.")

    required_columns = {
        date_column,
        quantity_column,
        unit_price_column,
    }

    missing_columns = required_columns - set(dataframe.columns)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(f"Missing required columns: {missing}")

    if dataframe.empty:
        raise ValueError("The dataset contains no rows.")

    data = dataframe[
        [date_column, quantity_column, unit_price_column]
    ].copy()

    # Parse dates and reject invalid or missing values.
    data[date_column] = pd.to_datetime(
        data[date_column],
        errors="coerce",
    )

    if data[date_column].isna().any():
        raise ValueError(
            f"Column '{date_column}' contains missing or invalid dates."
        )

    # Validate numeric fields.
    for column in (quantity_column, unit_price_column):
        data[column] = pd.to_numeric(data[column], errors="raise")

        if data[column].isna().any():
            raise ValueError(
                f"Column '{column}' cannot contain missing values."
            )

        if not data[column].map(
            lambda value: math.isfinite(float(value))
        ).all():
            raise ValueError(
                f"Column '{column}' must contain finite numbers."
            )

    quantities = data[quantity_column]
    prices = data[unit_price_column]

    if (quantities < 0).any():
        raise ValueError("Quantities cannot be negative.")

    if (quantities % 1 != 0).any():
        raise ValueError("Quantities must be whole numbers.")

    if (prices < 0).any():
        raise ValueError("Unit prices cannot be negative.")

    data[quantity_column] = quantities.astype("int64")

    data["_revenue"] = (
        data[quantity_column].astype("float64")
        * prices.astype("float64")
    )

    if not data["_revenue"].map(math.isfinite).all():
        raise ValueError(
            "Calculated revenue exceeds the supported numeric range."
        )

        # Normalize each row to the beginning of its reporting period.
    dates = data[date_column]

    if business_calendar is None:
        # Preserve existing behavior when no calendar is provided.
        if period == "day":
            data["_period_start"] = dates.dt.normalize()
        elif period == "week":
            data["_period_start"] = (
                dates.dt.to_period("W-SUN").dt.start_time
            )
        else:
            data["_period_start"] = (
                dates.dt.to_period("M").dt.start_time
            )

        grouped = (
            data.groupby("_period_start", sort=True)
            .agg(
                revenue=("_revenue", "sum"),
                units_sold=(quantity_column, "sum"),
            )
            .reset_index()
        )

    else:
        calendar = load_business_calendar(business_calendar)

        calendar_dates = calendar["date"]

        # The calendar must cover every calendar date in its range.
        gaps = calendar_dates.diff().dropna()

        if (gaps != pd.Timedelta(days=1)).any():
            raise ValueError(
                "The business calendar must contain every date "
                "in its date range."
            )

        sales_dates = dates.dt.normalize()

        # Every sales date must be covered by the calendar.
        if (
            sales_dates.min() < calendar_dates.min()
            or sales_dates.max() > calendar_dates.max()
        ):
            raise ValueError(
                "The business calendar does not cover all sales dates."
            )

        # Sales on non-business days must not be silently discarded.
        business_dates = set(
            calendar.loc[
                calendar["is_business_day"], "date"
            ]
        )

        non_business_sales = ~sales_dates.isin(business_dates)

        if non_business_sales.any():
            raise ValueError(
                "Sales records exist on non-business days."
            )

        # Aggregate transactions by their calendar date.
        data["_calendar_date"] = sales_dates

        daily_sales = (
            data.groupby("_calendar_date", sort=True)
            .agg(
                revenue=("_revenue", "sum"),
                units_sold=(quantity_column, "sum"),
            )
            .reset_index()
            .rename(columns={"_calendar_date": "date"})
        )

        # Start with the calendar, so business days without sales
        # are represented by zero revenue and zero units.
        business_days = calendar.loc[
            calendar["is_business_day"], ["date"]
        ].copy()

        business_days = business_days.merge(
            daily_sales,
            on="date",
            how="left",
        )

        business_days["revenue"] = (
            business_days["revenue"].fillna(0.0)
        )

        business_days["units_sold"] = (
            business_days["units_sold"].fillna(0).astype("int64")
        )

        if period == "day":
            business_days["_period_start"] = business_days["date"]
        elif period == "week":
            business_days["_period_start"] = (
                business_days["date"]
                .dt.to_period("W-SUN")
                .dt.start_time
            )
        else:
            business_days["_period_start"] = (
                business_days["date"]
                .dt.to_period("M")
                .dt.start_time
            )

        grouped = (
            business_days.groupby("_period_start", sort=True)
            .agg(
                revenue=("revenue", "sum"),
                units_sold=("units_sold", "sum"),
            )
            .reset_index()
        )

    if not grouped["revenue"].map(math.isfinite).all():
        raise ValueError(
            "Total revenue exceeds the supported numeric range."
        )

    total_units = int(data[quantity_column].sum())
    total_revenue = float(data["_revenue"].sum())

    if not math.isfinite(total_revenue):
        raise ValueError(
            "Total revenue exceeds the supported numeric range."
        )

    points = []
    previous_revenue = None

    for _, row in grouped.iterrows():
        current_revenue = float(row["revenue"])
        revenue_growth_percent = None

        if previous_revenue is not None and previous_revenue != 0:
            revenue_growth_percent = (
                (current_revenue - previous_revenue)
                / previous_revenue
            ) * 100

        points.append(
            SalesTrendPoint(
                period_start=row["_period_start"].strftime("%Y-%m-%d"),
                revenue=round(current_revenue, 2),
                units_sold=int(row["units_sold"]),
                revenue_growth_percent=(
                    round(revenue_growth_percent, 2)
                    if revenue_growth_percent is not None
                    else None
                ),
            )
        )

        previous_revenue = current_revenue

    return SalesTrend(
        period=period,
        row_count=len(data),
        total_units_sold=total_units,
        total_revenue=round(total_revenue, 2),
        trend=points,
    )


    