from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List


from app.api.health import router as health_router
from app.api.users import router as users_router
from app.api.images import router as images_router
from app.api.containers import router as containers_router

app = FastAPI(
    title="Orchestrator API",
    description="Container orchestration and management service",
    version="1.0.0"
)
app.include_router(health_router)
app.include_router(users_router)
app.include_router(images_router)
app.include_router(containers_router)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "Orchestrator API is running", "status": "healthy"}



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


