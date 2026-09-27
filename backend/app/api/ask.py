from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.container import container

router = APIRouter(tags=["ask"])


class AskRequest(BaseModel):
    paper_id: str
    question: str = Field(..., min_length=1)
    top_k: int = Field(5, ge=1, le=20)


class SourceChunk(BaseModel):
    chunk_id: int
    section: str
    page_number: int
    score: float


class AskResponse(BaseModel):
    paper_id: str
    question: str
    answer: str
    sources: list[SourceChunk]


@router.post("/ask", response_model=AskResponse)
def ask(body: AskRequest):
    # 1. Embed the query (with BGE prefix)
    query_vec = container.embedding_service.embed_query(body.question)

    # 2. Retrieve top chunks via hybrid search
    chunks = container.hybrid_search_service.search(
        paper_id=body.paper_id,
        embedding=query_vec,
        query=body.question,
        top_k=body.top_k,
    )

    if not chunks:
        return AskResponse(
            paper_id=body.paper_id,
            question=body.question,
            answer="I couldn't find any relevant content in this paper.",
            sources=[],
        )

    # 3. Build context from chunks (cap total length to keep prompt tight)
    context_parts = []
    for c in chunks:
        context_parts.append(
            f"[Section: {c.get('section', 'Unknown')} | "
            f"Page {c.get('page_number', '?')}]\n{c.get('text', '')}"
        )
    context = "\n\n".join(context_parts)

    # 4. Ask Gemini
    answer = container.llm_service.provider.generate(
        question=body.question,
        context=context,
    )

    # 5. Return answer + sources
    sources = [
        SourceChunk(
            chunk_id=c["chunk_id"],
            section=c.get("section", "Unknown"),
            page_number=c.get("page_number", 0),
            score=float(c.get("final_score", 0.0)),
        )
        for c in chunks
    ]

    return AskResponse(
        paper_id=body.paper_id,
        question=body.question,
        answer=answer,
        sources=sources,
    )