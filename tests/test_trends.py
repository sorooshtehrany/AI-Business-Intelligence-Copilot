import pandas as pd
import pytest

from app.services.trend_service import calculate_sales_trend
from fastapi.testclient import TestClient
from app.main import app


def sample_sales_data():
    return pd.DataFrame(
        {
            "date": [
                "2026-10-01",
                "2026-10-01",
                "2026-10-02",
                "2026-10-03",
                "2026-10-03",
                "2026-10-04",
            ],
            "product": [
                "Laptop",
                "Phone",
                "Laptop",
                "Tablet",
                "Phone",
                "Laptop",
            ],
            "quantity": [2, 3, 1, 4, 2, 3],
            "unit_price": [1000, 500, 1000, 300, 500, 1000],
        }
    )


def test_calculates_daily_sales_trend():
    result = calculate_sales_trend(
        sample_sales_data(),
        period="day",
    )

    assert result.period == "day"
    assert result.row_count == 6
    assert result.total_units_sold == 15
    assert result.total_revenue == 9700.0

    assert len(result.trend) == 4

    assert result.trend[0].period_start == "2026-10-01"
    assert result.trend[0].revenue == 3500.0
    assert result.trend[0].units_sold == 5

    assert result.trend[1].period_start == "2026-10-02"
    assert result.trend[1].revenue == 1000.0
    assert result.trend[1].units_sold == 1


def test_groups_sales_by_week():
    dataframe = pd.DataFrame(
        {
            "date": [
                "2026-10-04",  # Sunday
                "2026-10-05",  # Monday
            ],
            "quantity": [2, 3],
            "unit_price": [100, 200],
        }
    )

    result = calculate_sales_trend(dataframe, period="week")

    assert len(result.trend) == 2

    assert result.trend[0].period_start == "2026-09-28"
    assert result.trend[0].revenue == 200.0

    assert result.trend[1].period_start == "2026-10-05"
    assert result.trend[1].revenue == 600.0


def test_groups_sales_by_month():
    dataframe = pd.DataFrame(
        {
            "date": [
                "2026-10-01",
                "2026-10-20",
                "2026-11-02",
            ],
            "quantity": [2, 1, 3],
            "unit_price": [100, 100, 200],
        }
    )

    result = calculate_sales_trend(dataframe, period="month")

    assert len(result.trend) == 2

    assert result.trend[0].period_start == "2026-10-01"
    assert result.trend[0].revenue == 300.0
    assert result.trend[0].units_sold == 3

    assert result.trend[1].period_start == "2026-11-01"
    assert result.trend[1].revenue == 600.0
    assert result.trend[1].units_sold == 3


def test_rejects_invalid_dates():
    dataframe = pd.DataFrame(
        {
            "date": ["not-a-date"],
            "quantity": [1],
            "unit_price": [100],
        }
    )

    with pytest.raises(ValueError, match="invalid dates"):
        calculate_sales_trend(dataframe)


def test_rejects_negative_quantities():
    dataframe = pd.DataFrame(
        {
            "date": ["2026-10-01"],
            "quantity": [-1],
            "unit_price": [100],
        }
    )

    with pytest.raises(ValueError, match="Quantities cannot be negative"):
        calculate_sales_trend(dataframe)


def test_rejects_missing_columns():
    dataframe = pd.DataFrame(
        {
            "date": ["2026-10-01"],
            "quantity": [1],
        }
    )

    with pytest.raises(ValueError, match="Missing required columns"):
        calculate_sales_trend(dataframe)


def test_rejects_invalid_period():
    dataframe = sample_sales_data()

    with pytest.raises(ValueError, match="Period must be"):
        calculate_sales_trend(dataframe, period="year")





client = TestClient(app)


def test_sales_trend_endpoint_returns_daily_trend():
    csv_content = (
        "date,product,quantity,unit_price\n"
        "2026-10-01,Laptop,2,1000\n"
        "2026-10-01,Phone,3,500\n"
        "2026-10-02,Laptop,1,1000\n"
    )

    response = client.post(
        "/api/metrics/sales/trend?period=day",
        files={
            "file": (
                "sales.csv",
                csv_content.encode("utf-8"),
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["period"] == "day"
    assert result["row_count"] == 3
    assert result["total_units_sold"] == 6
    assert result["total_revenue"] == 4500.0

    assert len(result["trend"]) == 2

    assert result["trend"][0]["period_start"] == "2026-10-01"
    assert result["trend"][0]["revenue"] == 3500.0

    assert result["trend"][1]["period_start"] == "2026-10-02"
    assert result["trend"][1]["revenue"] == 1000.0

    assert result["trend"][0]["revenue_growth_percent"] is None
    assert result["trend"][1]["revenue_growth_percent"] == -71.43


def test_sales_trend_endpoint_rejects_invalid_period():
    csv_content = (
        "date,quantity,unit_price\n"
        "2026-10-01,2,100\n"
    )

    response = client.post(
        "/api/metrics/sales/trend?period=year",
        files={
            "file": (
                "sales.csv",
                csv_content.encode("utf-8"),
                "text/csv",
            )
        },
    )

    assert response.status_code == 422

def test_calculates_positive_revenue_growth():
    dataframe = pd.DataFrame({
        "date": ["2026-10-01", "2026-10-02"],
        "quantity": [10, 15],
        "unit_price": [100, 100],
    })

    result = calculate_sales_trend(dataframe, period="day")

    assert result.trend[0].revenue == 1000.0
    assert result.trend[0].revenue_growth_percent is None

    assert result.trend[1].revenue == 1500.0
    assert result.trend[1].revenue_growth_percent == 50.0


def test_calculates_negative_revenue_growth():
    dataframe = pd.DataFrame({
        "date": ["2026-10-01", "2026-10-02"],
        "quantity": [10, 5],
        "unit_price": [100, 100],
    })

    result = calculate_sales_trend(dataframe, period="day")

    assert result.trend[0].revenue == 1000.0
    assert result.trend[1].revenue == 500.0
    assert result.trend[1].revenue_growth_percent == -50.0


def test_returns_none_growth_when_previous_revenue_is_zero():


    dataframe = pd.DataFrame({
        "date": ["2026-10-01", "2026-10-02"],
        "quantity": [0, 5],
        "unit_price": [100, 100],
    })

    result = calculate_sales_trend(dataframe, period="day")

    assert result.trend[0].revenue == 0.0
    assert result.trend[0].revenue_growth_percent is None

    assert result.trend[1].revenue == 500.0
    assert result.trend[1].revenue_growth_percent is None




def test_calculates_positive_revenue_growth():
    dataframe = pd.DataFrame({
        "date": [
            "2026-10-01",
            "2026-10-02",
        ],
        "quantity": [10, 15],
        "unit_price": [100, 100],
    })

    result = calculate_sales_trend(dataframe, period="day")

    assert result.trend[0].revenue == 1000.0
    assert result.trend[0].revenue_growth_percent is None

    assert result.trend[1].revenue == 1500.0
    assert result.trend[1].revenue_growth_percent == 50.0


def test_calculates_negative_revenue_growth():
    dataframe = pd.DataFrame({
        "date": [
            "2026-10-01",
            "2026-10-02",
        ],
        "quantity": [10, 5],
        "unit_price": [100, 100],
    })

    result = calculate_sales_trend(dataframe, period="day")

    assert result.trend[0].revenue == 1000.0
    assert result.trend[1].revenue == 500.0
    assert result.trend[1].revenue_growth_percent == -50.0


def test_returns_none_growth_when_previous_revenue_is_zero():
    dataframe = pd.DataFrame({
        "date": [
            "2026-10-01",
            "2026-10-02",
        ],
        "quantity": [0, 5],
        "unit_price": [100, 100],
    })

    result = calculate_sales_trend(dataframe, period="day")

    assert result.trend[0].revenue == 0.0
    assert result.trend[0].revenue_growth_percent is None

    assert result.trend[1].revenue == 500.0
    assert result.trend[1].revenue_growth_percent is None


def test_sales_trend_endpoint_accepts_business_calendar():
    sales_csv = (
        "date,quantity,unit_price\n"
        "2026-10-01,10,100\n"
        "2026-10-02,15,100\n"
        "2026-10-05,20,100\n"
    )

    calendar_csv = (
        "date,is_business_day\n"
        "2026-10-01,true\n"
        "2026-10-02,true\n"
        "2026-10-03,false\n"
        "2026-10-04,true\n"
        "2026-10-05,true\n"
    )

    response = client.post(
        "/api/metrics/sales/trend?period=day",
        files={
            "file": (
                "sales.csv",
                sales_csv.encode("utf-8"),
                "text/csv",
            ),
            "business_calendar_file": (
                "business_calendar.csv",
                calendar_csv.encode("utf-8"),
                "text/csv",
            ),
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["row_count"] == 3
    assert result["total_units_sold"] == 45
    assert result["total_revenue"] == 4500.0

    assert [
        point["period_start"] for point in result["trend"]
    ] == [
        "2026-10-01",
        "2026-10-02",
        "2026-10-04",
        "2026-10-05",
    ]

    assert result["trend"][2]["revenue"] == 0.0
    assert result["trend"][2]["units_sold"] == 0
    assert result["trend"][2]["revenue_growth_percent"] == -100.0

    # The previous business day's revenue was zero.
    assert result["trend"][3]["revenue_growth_percent"] is None


def test_sales_trend_endpoint_rejects_calendar_with_missing_columns():
    sales_csv = (
        "date,quantity,unit_price\n"
        "2026-10-01,2,100\n"
    )

    invalid_calendar_csv = (
        "date,holiday\n"
        "2026-10-01,false\n"
    )

    response = client.post(
        "/api/metrics/sales/trend",
        files={
            "file": (
                "sales.csv",
                sales_csv.encode("utf-8"),
                "text/csv",
            ),
            "business_calendar_file": (
                "business_calendar.csv",
                invalid_calendar_csv.encode("utf-8"),
                "text/csv",
            ),
        },
    )

    assert response.status_code == 422
    assert "Missing required calendar columns" in response.json()["detail"]


def test_sales_trend_endpoint_rejects_non_csv_calendar():
    sales_csv = (
        "date,quantity,unit_price\n"
        "2026-10-01,2,100\n"
    )

    response = client.post(
        "/api/metrics/sales/trend",
        files={
            "file": (
                "sales.csv",
                sales_csv.encode("utf-8"),
                "text/csv",
            ),
            "business_calendar_file": (
                "business_calendar.txt",
                b"invalid calendar",
                "text/plain",
            ),
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == (
    "Business calendar: only CSV files are supported."
)


def test_sales_trend_endpoint_rejects_empty_calendar():
    sales_csv = (
        "date,quantity,unit_price\n"
        "2026-10-01,2,100\n"
    )

    response = client.post(
        "/api/metrics/sales/trend",
        files={
            "file": (
                "sales.csv",
                sales_csv.encode("utf-8"),
                "text/csv",
            ),
            "business_calendar_file": (
                "business_calendar.csv",
                b"",
                "text/csv",
            ),
        },
    )

    assert response.status_code == 400