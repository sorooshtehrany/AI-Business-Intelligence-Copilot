from fastapi import APIRouter
router = APIRouter()
@router.get("/")
def root():
    return{
           "message": "AI Business Intelligence Copilot is running",
           "version": "0.1.0",
          }
@router.get("/health")
def health_check():
    return{
           "status": "healthy",
         }
