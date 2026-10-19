import pandas as pd
import pytest

from app.services.trend_service import calculate_sales_trend


def make_sales_data():
    return pd.DataFrame({
        "date": [
            "2026-10-01",
            "2026-10-02",
            "2026-10-05",
        ],
        "quantity": [10, 15, 20],
        "unit_price": [100, 100, 100],
    })


def make_business_calendar():
    return pd.DataFrame({
        "date": [
            "2026-10-01",
            "2026-10-02",
            "2026-10-03",
            "2026-10-04",
            "2026-10-05",
        ],
        "is_business_day": [
            True,
            True,
            False,
            True,
            True,
        ],
    })


def test_business_days_without_sales_are_included():
    sales = make_sales_data()
    calendar = make_business_calendar()

    result = calculate_sales_trend(
        dataframe=sales,
        period="day",
        business_calendar=calendar,
    )

    assert len(result.trend) == 4

    assert [
        point.period_start for point in result.trend
    ] == [
        "2026-10-01",
        "2026-10-02",
        "2026-10-04",
        "2026-10-05",
    ]

    assert result.trend[2].revenue == 0.0
    assert result.trend[2].units_sold == 0


def test_non_business_days_are_excluded():
    result = calculate_sales_trend(
        dataframe=make_sales_data(),
        period="day",
        business_calendar=make_business_calendar(),
    )

    dates = [
        point.period_start for point in result.trend
    ]

    assert "2026-10-03" not in dates


def test_growth_uses_previous_business_day():
    result = calculate_sales_trend(
        dataframe=make_sales_data(),
        period="day",
        business_calendar=make_business_calendar(),
    )

    # October 1: revenue = 1000; first point has no growth.
    assert result.trend[0].revenue == 1000.0
    assert result.trend[0].revenue_growth_percent is None

    # October 2: revenue = 1500; growth = 50%.
    assert result.trend[1].revenue == 1500.0
    assert result.trend[1].revenue_growth_percent == 50.0

    # October 4: zero revenue after October 2.
    assert result.trend[2].revenue == 0.0
    assert result.trend[2].revenue_growth_percent == -100.0

    # October 5: previous business day's revenue was zero.
    assert result.trend[3].revenue == 2000.0
    assert result.trend[3].revenue_growth_percent is None


def test_rejects_calendar_with_missing_dates():
    sales = pd.DataFrame({
        "date": ["2026-10-01"],
        "quantity": [1],
        "unit_price": [100],
    })

    calendar = pd.DataFrame({
        "date": [
            "2026-10-01",
            "2026-10-03",
        ],
        "is_business_day": [
            True,
            True,
        ],
    })

    with pytest.raises(
        ValueError,
        match="must contain every date",
    ):
        calculate_sales_trend(
            dataframe=sales,
            period="day",
            business_calendar=calendar,
        )


def test_rejects_sales_on_non_business_days():
    sales = pd.DataFrame({
        "date": ["2026-10-03"],
        "quantity": [1],
        "unit_price": [100],
    })

    calendar = make_business_calendar()

    with pytest.raises(
        ValueError,
        match="Sales records exist on non-business days",
    ):
        calculate_sales_trend(
            dataframe=sales,
            period="day",
            business_calendar=calendar,
        )


@pytest.mark.parametrize(
    ("period", "expected_starts", "expected_revenues", "expected_units"),
    [
        (
            "week",
            ["2026-09-28", "2026-10-05"],
            [2500.0, 2000.0],
            [25, 20],
        ),
        (
            "month",
            ["2026-10-01"],
            [4500.0],
            [45],
        ),
    ],
)
def test_groups_business_day_revenue_by_period(
    period,
    expected_starts,
    expected_revenues,
    expected_units,
):
    result = calculate_sales_trend(
        dataframe=make_sales_data(),
        period=period,
        business_calendar=make_business_calendar(),
    )

    assert [
        point.period_start for point in result.trend
    ] == expected_starts

    assert [
        point.revenue for point in result.trend
    ] == expected_revenues

    assert [
        point.units_sold for point in result.trend
    ] == expected_units