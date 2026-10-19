import pandas as pd
import pytest

from app.services.metrics_service import calculate_sales_metrics
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_calculates_sales_metrics():
    dataframe = pd.DataFrame(
        {
            "product": ["Laptop", "Phone", "Tablet", "Laptop"],
            "quantity": [2, 5, 3, 1],
            "unit_price": [1000, 500, 300, 1000],
        }
    )

    result = calculate_sales_metrics(dataframe)

    assert result.row_count == 4
    assert result.total_units_sold == 11
    assert result.total_revenue == 6400.0
    assert result.average_unit_price == 581.82
    assert result.distinct_products == 3
    assert result.top_product_by_quantity == "Phone"
    assert result.top_product_by_revenue == "Laptop"


def test_calculates_metrics_for_each_product():
    dataframe = pd.DataFrame(
        {
            "product": ["Laptop", "Phone", "Laptop"],
            "quantity": [2, 3, 1],
            "unit_price": [1000, 500, 1000],
        }
    )

    result = calculate_sales_metrics(dataframe)

    products = {item.product: item for item in result.products}

    assert products["Laptop"].units_sold == 3
    assert products["Laptop"].revenue == 3000.0

    assert products["Phone"].units_sold == 3
    assert products["Phone"].revenue == 1500.0


def test_rejects_missing_columns():
    dataframe = pd.DataFrame(
        {
            "product": ["Laptop"],
            "quantity": [2],
        }
    )

    with pytest.raises(ValueError, match="Missing required columns"):
        calculate_sales_metrics(dataframe)


def test_rejects_negative_quantities():
    dataframe = pd.DataFrame(
        {
            "product": ["Laptop"],
            "quantity": [-1],
            "unit_price": [1000],
        }
    )

    with pytest.raises(ValueError, match="Quantities cannot be negative"):
        calculate_sales_metrics(dataframe)


def test_rejects_negative_prices():
    dataframe = pd.DataFrame(
        {
            "product": ["Laptop"],
            "quantity": [1],
            "unit_price": [-100],
        }
    )

    with pytest.raises(ValueError, match="Unit prices cannot be negative"):
        calculate_sales_metrics(dataframe)


def test_returns_none_average_when_total_quantity_is_zero():
    dataframe = pd.DataFrame(
        {
            "product": ["Laptop"],
            "quantity": [0],
            "unit_price": [1000],
        }
    )

    result = calculate_sales_metrics(dataframe)

    assert result.total_units_sold == 0
    assert result.total_revenue == 0.0
    assert result.average_unit_price is None




def test_sales_metrics_endpoint_returns_metrics():
    csv_content = (
        "product,quantity,unit_price\n"
        "Laptop,2,1000\n"
        "Phone,5,500\n"
        "Tablet,3,300\n"
        "Laptop,1,1000\n"
    )

    response = client.post(
        "/api/metrics/sales",
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

    assert result["row_count"] == 4
    assert result["total_units_sold"] == 11
    assert result["total_revenue"] == 6400.0
    assert result["average_unit_price"] == 581.82
    assert result["distinct_products"] == 3
    assert result["top_product_by_quantity"] == "Phone"
    assert result["top_product_by_revenue"] == "Laptop"
    assert len(result["products"]) == 3


def test_sales_metrics_endpoint_rejects_non_csv_files():
    response = client.post(
        "/api/metrics/sales",
        files={
            "file": (
                "sales.txt",
                b"some content",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only CSV files are supported."