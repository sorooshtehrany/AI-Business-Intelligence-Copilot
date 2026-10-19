import pandas as pd
import pytest

from app.services.calendar_service import load_business_calendar


def test_loads_and_sorts_business_calendar():
    dataframe = pd.DataFrame({
        "date": [
            "2026-10-02",
            "2026-10-01",
            "2026-10-03",
        ],
        "is_business_day": [
            "true",
            "true",
            "false",
        ],
    })

    result = load_business_calendar(dataframe)

    assert result["date"].dt.strftime("%Y-%m-%d").tolist() == [
        "2026-10-01",
        "2026-10-02",
        "2026-10-03",
    ]

    assert result["is_business_day"].tolist() == [
        True,
        True,
        False,
    ]


def test_rejects_missing_calendar_columns():
    dataframe = pd.DataFrame({
        "date": ["2026-10-01"],
    })

    with pytest.raises(
        ValueError,
        match="Missing required calendar columns",
    ):
        load_business_calendar(dataframe)


def test_rejects_invalid_calendar_dates():
    dataframe = pd.DataFrame({
        "date": ["not-a-date"],
        "is_business_day": ["true"],
    })

    with pytest.raises(
        ValueError,
        match="invalid dates",
    ):
        load_business_calendar(dataframe)


def test_rejects_duplicate_calendar_dates():
    dataframe = pd.DataFrame({
        "date": [
            "2026-10-01",
            "2026-10-01",
        ],
        "is_business_day": [
            "true",
            "false",
        ],
    })

    with pytest.raises(
        ValueError,
        match="duplicate dates",
    ):
        load_business_calendar(dataframe)


def test_rejects_invalid_business_day_values():
    dataframe = pd.DataFrame({
        "date": ["2026-10-01"],
        "is_business_day": ["maybe"],
    })

    with pytest.raises(
        ValueError,
        match="true or false",
    ):
        load_business_calendar(dataframe)


def test_rejects_empty_calendar():
    dataframe = pd.DataFrame({
        "date": pd.Series(dtype="object"),
        "is_business_day": pd.Series(dtype="object"),
    })

    with pytest.raises(
        ValueError,
        match="contains no rows",
    ):
        load_business_calendar(dataframe)
