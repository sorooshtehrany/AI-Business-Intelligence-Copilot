import pandas as pd


REQUIRED_COLUMNS = {"date", "is_business_day"}


def load_business_calendar(dataframe: pd.DataFrame) -> pd.DataFrame:
    """
    Validate and normalize a business calendar.

    Required columns:
        date: Calendar date.
        is_business_day: Whether the date is a business day.

    Returns:
        A DataFrame containing normalized dates and boolean
        is_business_day values.
    """

    missing_columns = REQUIRED_COLUMNS - set(dataframe.columns)

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))
        raise ValueError(
            f"Missing required calendar columns: {missing}"
        )

    if dataframe.empty:
        raise ValueError("The business calendar contains no rows.")

    calendar = dataframe[
        ["date", "is_business_day"]
    ].copy()

    # Parse dates and normalize them to midnight.
    calendar["date"] = pd.to_datetime(
        calendar["date"],
        errors="coerce",
    )

    if calendar["date"].isna().any():
        raise ValueError(
            "The calendar contains missing or invalid dates."
        )

    calendar["date"] = calendar["date"].dt.normalize()

    # A calendar must not contain multiple entries for one date.
    if calendar["date"].duplicated().any():
        raise ValueError(
            "The business calendar contains duplicate dates."
        )

    # Accept explicit boolean values and common CSV representations.
    def parse_business_day(value: object) -> bool:
        if pd.isna(value):
            raise ValueError(
                "The is_business_day column cannot contain missing values."
            )

        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            normalized = value.strip().lower()

            if normalized == "true":
                return True

            if normalized == "false":
                return False

        raise ValueError(
            "The is_business_day column must contain only "
            "true or false values."
        )

    calendar["is_business_day"] = calendar[
        "is_business_day"
    ].map(parse_business_day)

    return calendar.sort_values("date").reset_index(drop=True)

