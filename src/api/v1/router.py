from fastapi import APIRouter

from src.execution.router import router as execution_router

router = APIRouter()
router.include_router(execution_router)
