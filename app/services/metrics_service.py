import math

import pandas as pd

from app.schemas.metrics import ProductMetric, SalesMetrics


def calculate_sales_metrics(
    dataframe: pd.DataFrame,
    product_column: str = "product",
    quantity_column: str = "quantity",
    unit_price_column: str = "unit_price",
) -> SalesMetrics:
    required_columns = {
        product_column,
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
        [product_column, quantity_column, unit_price_column]
    ].copy()

    data[product_column] = data[product_column].astype("string").str.strip()

    if data[product_column].isna().any() or data[product_column].eq("").any():
        raise ValueError("Product names cannot be empty.")

    for column in [quantity_column, unit_price_column]:
        data[column] = pd.to_numeric(data[column], errors="raise")

        if data[column].isna().any():
            raise ValueError(f"Column '{column}' cannot contain missing values.")

        if not data[column].map(
            lambda value: math.isfinite(float(value))
        ).all():
            raise ValueError(f"Column '{column}' must contain finite numbers.")

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
        * data[unit_price_column].astype("float64")
    )

    if not data["_revenue"].map(math.isfinite).all():
        raise ValueError("Calculated revenue exceeds the supported numeric range.")

    grouped = (
        data.groupby(product_column, sort=True)
        .agg(
            units_sold=(quantity_column, "sum"),
            revenue=("_revenue", "sum"),
        )
        .reset_index()
    )

    if not grouped["revenue"].map(math.isfinite).all():
        raise ValueError("Total revenue exceeds the supported numeric range.")

    grouped["revenue"] = grouped["revenue"].round(2)

    total_units = int(data[quantity_column].sum())
    total_revenue = float(data["_revenue"].sum())

    if not math.isfinite(total_revenue):
        raise ValueError("Total revenue exceeds the supported numeric range.")

    total_revenue = round(total_revenue, 2)

    average_unit_price = (
        round(total_revenue / total_units, 2)
        if total_units > 0
        else None
    )

    top_quantity = grouped.sort_values(
        ["units_sold", product_column],
        ascending=[False, True],
    ).iloc[0][product_column]

    top_revenue = grouped.sort_values(
        ["revenue", product_column],
        ascending=[False, True],
    ).iloc[0][product_column]

    products = [
        ProductMetric(
            product=str(row[product_column]),
            units_sold=int(row["units_sold"]),
            revenue=float(row["revenue"]),
        )
        for _, row in grouped.iterrows()
    ]

    return SalesMetrics(
        row_count=len(data),
        total_units_sold=total_units,
        total_revenue=total_revenue,
        average_unit_price=average_unit_price,
        distinct_products=len(grouped),
        top_product_by_quantity=str(top_quantity),
        top_product_by_revenue=str(top_revenue),
        products=products,
    )