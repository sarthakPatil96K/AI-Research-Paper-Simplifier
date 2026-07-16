from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.search import router as search_router
from app.api.upload import router as upload_router
from app.api.chat import router as chat_router

app = FastAPI(
    title="AI Research Paper Simplifier"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    upload_router,
    prefix="/api",
    tags=["Upload"]
)

app.include_router(
    search_router,
    prefix="/api",
    tags=["Semantic Search"]
)

app.include_router(
    chat_router,
    prefix="/api",
    tags=["Chat"]
)
@app.get("/")
def root():
    return {
        "message": "Backend Running Successfully"
    }