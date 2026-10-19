
from fastapi import FastAPI

from app.api.datasets import router as datasets_router
from app.api.health import router as health_router
from app.api.metrics import router as metrics_router
from app.api.trends import router as trends_router


app = FastAPI(
    title="AI Business Intelligence Copilot",
    version="0.1.0",
    description="An AI-powered business intelligence and data analysis platform.",
)

app.include_router(health_router)
app.include_router(datasets_router)
app.include_router(metrics_router)
app.include_router(trends_router)
