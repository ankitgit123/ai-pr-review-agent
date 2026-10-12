
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.api.routes.reviews import router as reviews_router
from app.api.routes.github import router as github_router
from app.api.routes.review_workflow import router as review_workflow_router

from app.db.session import SessionLocal, get_db

app = FastAPI(
    title="AI PR Review Agent",
    description="An AI-powered GitHub pull request review service.",
    version="0.1.0",
)

app.include_router(github_router)
app.include_router(reviews_router)
app.include_router(review_workflow_router)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "ai-pr-review-agent",
    }


@app.get("/health/db")
def database_health_check(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1")).scalar_one()
        return {
            "status": "healthy",
            "database": "mysql",
            "query_result": result,
        }
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="Database connection or query failed",
        ) from exc
