from io import BytesIO

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.metrics import SalesMetrics
from app.services.metrics_service import calculate_sales_metrics


router = APIRouter(
    prefix="/api/metrics",
    tags=["Business Metrics"],
)

MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024


@router.post("/sales", response_model=SalesMetrics)
async def calculate_sales(
    file: UploadFile = File(...),
) -> SalesMetrics:
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(
            status_code=400,
            detail="Only CSV files are supported.",
        )

    content = await file.read(MAX_UPLOAD_SIZE_BYTES + 1)

    if len(content) > MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="File size exceeds the 10 MB limit.",
        )

    if not content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
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
            detail="The CSV file is invalid or cannot be parsed.",
        ) from exc

    if len(dataframe.columns) == 0:
        raise HTTPException(
            status_code=400,
            detail="The CSV file contains no columns.",
        )

    try:
        return calculate_sales_metrics(dataframe)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc