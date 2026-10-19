
from io import BytesIO

import pandas as pd
from fastapi import APIRouter, File, HTTPException, UploadFile

from app.schemas.dataset import DatasetProfile
from app.services.dataset_service import profile_dataframe

MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

router = APIRouter(
    prefix="/api/datasets",
    tags=["Datasets"],
)


@router.post("/profile", response_model=DatasetProfile)
async def profile_csv(
    
    file: UploadFile = File(...),
) -> DatasetProfile:
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

    return profile_dataframe(
        dataframe=dataframe,
        filename=file.filename,
    )
