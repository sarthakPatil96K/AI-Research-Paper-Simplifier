import json
import os
from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.container import container

router = APIRouter(tags=["papers"])

METADATA_DIR = "vector_db/metadata"
SUMMARY_DIR = "storage/summaries"
UPLOAD_DIR = "uploads"


class PaperListItem(BaseModel):
    paper_id: str
    title: str
    author: str
    page_count: int
    total_chunks: int | None = None
    uploaded_at: str | None = None


@router.get("/papers", response_model=list[PaperListItem])
def list_papers():
    if not os.path.exists(METADATA_DIR):
        return []

    items = []
    for fname in sorted(os.listdir(METADATA_DIR)):
        if not fname.endswith(".json"):
            continue
        paper_id = fname[:-5]
        path = os.path.join(METADATA_DIR, fname)
        try:
            with open(path) as f:
                data = json.load(f)
        except Exception:
            continue

        meta = data.get("metadata", data)
        items.append(
            PaperListItem(
                paper_id=paper_id,
                title=meta.get("title") or "Untitled",
                author=meta.get("author") or "Unknown",
                page_count=int(meta.get("page_count", 0)),
                total_chunks=data.get("total_chunks"),
                uploaded_at=data.get("uploaded_at"),
            )
        )
    return items


@router.get("/paper/{paper_id}")
def get_paper(paper_id: str):
    meta_path = os.path.join(METADATA_DIR, f"{paper_id}.json")
    if not os.path.exists(meta_path):
        raise HTTPException(404, f"Paper {paper_id} not found")

    with open(meta_path) as f:
        data = json.load(f)

    # Attach summary if it exists
    summary_path = os.path.join(SUMMARY_DIR, f"{paper_id}.json")
    summary = None
    if os.path.exists(summary_path):
        with open(summary_path) as f:
            summary = json.load(f).get("summary")

    return {
        "paper_id": paper_id,
        "metadata": data.get("metadata", {}),
        "total_chunks": data.get("total_chunks"),
        "summary": summary,
    }


@router.get("/paper/{paper_id}/chunks")
def get_paper_chunks(paper_id: str):
    """Debug helper — returns all chunks for a paper."""
    bm25_path = os.path.join("vector_db", "bm25", f"{paper_id}.pkl")
    if not os.path.exists(bm25_path):
        raise HTTPException(404, "Paper index not found")

    import pickle
    with open(bm25_path, "rb") as f:
        data = pickle.load(f)

    chunks = data.get("chunks", [])
    # Strip the text for the list, but keep it available
    return {
        "paper_id": paper_id,
        "count": len(chunks),
        "chunks": [
            {
                "chunk_id": c.get("chunk_id"),
                "section": c.get("section"),
                "page_number": c.get("page_number"),
                "word_count": c.get("word_count"),
                "text": c.get("text"),
            }
            for c in chunks
        ],
    }

import pickle
from app.core.container import container


@router.post("/paper/{paper_id}/regenerate-summary")
def regenerate_summary(paper_id: str):
    bm25_path = os.path.join("vector_db", "bm25", f"{paper_id}.pkl")
    if not os.path.exists(bm25_path):
        raise HTTPException(404, "Paper index not found")

    with open(bm25_path, "rb") as f:
        data = pickle.load(f)

    chunks = data.get("chunks", [])
    if not chunks:
        raise HTTPException(400, "No chunks available for this paper")

    summary = container.summary_service.generate_summary(paper_id, chunks)
    return {"paper_id": paper_id, "summary": summary}