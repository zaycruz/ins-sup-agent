from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.routes import health, jobs, contacts
from src.db.connection import init_db, close_pool


FRONTEND_DIR = Path(__file__).parent.parent.parent / "frontend"


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield
    await close_pool()


app = FastAPI(
    lifespan=lifespan,
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
app.include_router(contacts.router, prefix="/v1", tags=["Contacts"])


@app.get("/", include_in_schema=False)
async def root():
    if FRONTEND_DIR.exists() and (FRONTEND_DIR / "index.html").exists():
        return FileResponse(FRONTEND_DIR / "index.html")
    return {
        "name": "Insurance Supplementation Agent System",
        "version": "1.0.0",
        "docs": "/v1/docs",
        "upload": "/upload",
    }


@app.get("/upload", include_in_schema=False)
async def upload_page():
    return FileResponse(FRONTEND_DIR / "index.html")
