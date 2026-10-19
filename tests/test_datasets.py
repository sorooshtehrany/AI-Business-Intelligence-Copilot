
from io import BytesIO

import pandas as pd
from fastapi.testclient import TestClient

from app.main import app
from app.services.dataset_service import profile_dataframe

from app.api.datasets import MAX_UPLOAD_SIZE_BYTES

client = TestClient(app)


def test_profile_dataframe_returns_basic_statistics():
    dataframe = pd.DataFrame(
        {
            "product": ["A", "B", "A"],
            "quantity": [2, 4, 2],
            "revenue": [100.0, 200.0, 100.0],
        }
    )

    result = profile_dataframe(dataframe, "sales.csv")

    assert result.filename == "sales.csv"
    assert result.row_count == 3
    assert result.column_count == 3
    assert result.duplicate_rows == 1

    revenue = next(
        column
        for column in result.columns
        if column.name == "revenue"
    )

    assert revenue.numeric_statistics is not None
    assert revenue.numeric_statistics.mean == 400 / 3
    assert revenue.numeric_statistics.min == 100.0
    assert revenue.numeric_statistics.max == 200.0


def test_profile_dataframe_counts_missing_values():
    dataframe = pd.DataFrame(
        {
            "quantity": [10.0, None, 30.0],
        }
    )

    result = profile_dataframe(dataframe, "inventory.csv")

    assert result.columns[0].missing_values == 1
    assert result.columns[0].unique_values == 2


def test_profile_endpoint_returns_dataset_profile():
    csv_content = b"product,quantity,revenue\nA,2,100\nB,4,200\n"

    response = client.post(
        "/api/datasets/profile",
        files={
            "file": (
                "sales.csv",
                BytesIO(csv_content),
                "text/csv",
            )
        },
    )

    assert response.status_code == 200

    result = response.json()

    assert result["filename"] == "sales.csv"
    assert result["row_count"] == 2
    assert result["column_count"] == 3

    revenue = next(
        column
        for column in result["columns"]
        if column["name"] == "revenue"
    )

    assert revenue["numeric_statistics"]["mean"] == 150.0


def test_profile_endpoint_rejects_non_csv_files():
    response = client.post(
        "/api/datasets/profile",
        files={
            "file": (
                "sales.txt",
                b"some text",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400


def test_profile_endpoint_rejects_empty_files():
    response = client.post(
        "/api/datasets/profile",
        files={
            "file": (
                "empty.csv",
                b"",
                "text/csv",
            )
        },
    )

    assert response.status_code == 400


    def test_profile_detects_empty_columns_and_duplicates():
        dataframe = pd.DataFrame(
        {
            "product": ["Laptop", "Laptop", "Phone"],
            "quantity": [2, 2, 5],
            "notes": [None, None, None],
        }
        )

        result = profile_dataframe(dataframe, "sales.csv")

        assert result.duplicate_rows == 1

        issue_codes = {
            issue.code
            for issue in result.quality_issues
        }

        assert "DUPLICATE_ROWS" in issue_codes
        assert "EMPTY_COLUMN" in issue_codes

        empty_column_issue = next(
            issue
            for issue in result.quality_issues
            if issue.code == "EMPTY_COLUMN"
        )

        assert empty_column_issue.column == "notes"
        assert empty_column_issue.affected_rows == 3


def test_profile_excludes_infinite_values_from_statistics():
    dataframe = pd.DataFrame(
        {
            "revenue": [100.0, float("inf"), 300.0],
        }
    )

    result = profile_dataframe(dataframe, "sales.csv")

    revenue = next(
        column
        for column in result.columns
        if column.name == "revenue"
    )

    assert revenue.numeric_statistics is not None
    assert revenue.numeric_statistics.mean == 200.0
    assert revenue.numeric_statistics.min == 100.0
    assert revenue.numeric_statistics.max == 300.0

    issue = next(
        issue
        for issue in result.quality_issues
        if issue.code == "NON_FINITE_VALUES"
    )

    assert issue.column == "revenue"
    assert issue.affected_rows == 1




def test_profile_endpoint_rejects_oversized_files():
    content = b"x" * (MAX_UPLOAD_SIZE_BYTES + 1)

    response = client.post(
        "/api/datasets/profile",
        files={
            "file": (
                "large.csv",
                content,
                "text/csv",
            )
        },
    )

    assert response.status_code == 413



def test_profile_detects_empty_columns():

    dataframe = pd.DataFrame(
        {
            "product": ["Laptop", "Phone"],
            "notes": [None, None],
        }
    )

    result = profile_dataframe(dataframe, "sales.csv")

    empty_column_issues = [
        issue
        for issue in result.quality_issues
        if issue.code == "EMPTY_COLUMN"
    ]

    assert len(empty_column_issues) == 1
    assert empty_column_issues[0].column == "notes"
    assert empty_column_issues[0].affected_rows == 2