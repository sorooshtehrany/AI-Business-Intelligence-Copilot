from io import BytesIO
from typing import Annotated

import pandas as pd
from fastapi import APIRouter, File, HTTPException, Query, UploadFile

from app.schemas.trends import SalesTrend, TrendPeriod
from app.services.trend_service import calculate_sales_trend

router = APIRouter(
    prefix="/api/metrics/sales",
    tags=["Sales Trend Analysis"],
)

MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024


async def _read_csv_upload(
    uploaded_file: UploadFile,
    file_label: str,
) -> pd.DataFrame:
    """Validate and parse an uploaded CSV file."""

    if (
        not uploaded_file.filename
        or not uploaded_file.filename.lower().endswith(".csv")
    ):
        raise HTTPException(
            status_code=400,
            detail=f"{file_label}: only CSV files are supported.",
        )

    content = await uploaded_file.read(MAX_UPLOAD_SIZE_BYTES + 1)

    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"{file_label}: file size exceeds the 10 MB limit.",
        )

    if not content:
        raise HTTPException(
            status_code=400,
            detail=f"{file_label}: the uploaded file is empty.",
        )

    try:
        dataframe = pd.read_csv(BytesIO(content))
    except (
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        UnicodeDecodeError,
    ) as exc:
        raise HTTPException(
            status_code=400,
            detail=f"{file_label}: the CSV file is invalid or cannot be parsed.",
        ) from exc

    if len(dataframe.columns) == 0:
        raise HTTPException(
            status_code=400,
            detail=f"{file_label}: the CSV file contains no columns.",
        )

    return dataframe


@router.post("/trend", response_model=SalesTrend)
async def sales_trend(
    file: UploadFile = File(...),
    period: Annotated[TrendPeriod, Query()] = "day",
    business_calendar_file: UploadFile | None = File(None),
) -> SalesTrend:
    """Calculate sales trends, optionally using a business calendar."""

    sales_dataframe = await _read_csv_upload(
        uploaded_file=file,
        file_label="Sales file",
    )

    calendar_dataframe = None

    if business_calendar_file is not None:
        calendar_dataframe = await _read_csv_upload(
            uploaded_file=business_calendar_file,
            file_label="Business calendar",
        )

    try:
        return calculate_sales_trend(
            dataframe=sales_dataframe,
            period=period,
            business_calendar=calendar_dataframe,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
