import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api.search import router as search_router
from app.api.upload import router as upload_router
from app.api.chat import router as chat_router
from app.api.summary import router as summary_router
from app.api.ask import router as ask_router
from app.api.papers import router as papers_router


app = FastAPI(
    title="AI Research Paper Simplifier"
)

# ---------- CORS ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",   # Vite dev server
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",   # serve static UI from same origin
        "http://127.0.0.1:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Routers ----------
app.include_router(
    summary_router,
    prefix="/api",
    tags=["Summary"],
)

app.include_router(
    upload_router,
    prefix="/api",
    tags=["Upload"],
)

app.include_router(
    search_router,
    prefix="/api",
    tags=["Semantic Search"],
)

app.include_router(
    chat_router,
    prefix="/api",
    tags=["Chat"],
)

app.include_router(
    ask_router,
    prefix="/api",
    tags=["Ask"],
)

app.include_router(
    papers_router,
    prefix="/api",
    tags=["Papers"],
)

# ---------- Static UI ----------
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

if os.path.isdir(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(os.path.join(STATIC_DIR, "index.html"))
else:
    @app.get("/", include_in_schema=False)
    def root():
        return {"message": "Backend Running Successfully"}