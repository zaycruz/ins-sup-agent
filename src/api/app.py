from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routes import health, jobs


app = FastAPI(
    title="Insurance Supplementation Agent System",
    description="Multi-agent AI system for roofing insurance supplement generation",
    version="1.0.0",
    docs_url="/v1/docs",
    redoc_url="/v1/redoc",
    openapi_url="/v1/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, tags=["Health"])
app.include_router(jobs.router, prefix="/v1", tags=["Jobs"])


@app.get("/", include_in_schema=False)
async def root():
    return {
        "name": "Insurance Supplementation Agent System",
        "version": "1.0.0",
        "docs": "/v1/docs",
    }
