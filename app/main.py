from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.router import router as auth_router
from app.routers.admin import router as admin_router
from app.routers.articles import router as articles_router
from app.routers.clusters import router as clusters_router
from app.routers.digest import router as digest_router
from app.routers.outlets import router as outlets_router
from app.routers.users import router as users_router

app = FastAPI(
    title="Vernier News",
    description="Global media intelligence platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tightened once domain is known
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_PREFIX = "/api/v1"

app.include_router(auth_router, prefix=API_PREFIX)
app.include_router(admin_router, prefix=API_PREFIX)
app.include_router(articles_router, prefix=API_PREFIX)
app.include_router(clusters_router, prefix=API_PREFIX)
app.include_router(outlets_router, prefix=API_PREFIX)
app.include_router(users_router, prefix=API_PREFIX)
app.include_router(digest_router, prefix=API_PREFIX)


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok", "version": app.version}
