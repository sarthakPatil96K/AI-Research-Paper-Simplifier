from fastapi import APIRouter, HTTPException

from app.schemas.chat_schema import ChatRequest
from app.core.container import container

router = APIRouter()


@router.post("/chat")
def chat(request: ChatRequest):

    # Generate query embedding
    query_embedding = container.embedding_service.embed_query(
        request.question
    )

    # Retrieve relevant chunks
    chunks = container.hybrid_search_service.search(
        paper_id=request.paper_id,
        embedding=query_embedding,
        query=request.question,
        top_k=request.top_k
    )

    if len(chunks) == 0:
        raise HTTPException(
            status_code=404,
            detail="No relevant content found for this paper."
        )

    # Build structured context
    context_parts = []

    for chunk in chunks:

        context_parts.append(
            f"""
==============================
Section: {chunk['section']}
Page: {chunk['page_number']}

{chunk['text']}
==============================
""".strip()
        )

    context = "\n\n".join(context_parts)

    # Ask the LLM
    answer = container.llm_service.answer(
        request.question,
        context
    )

    # Prepare source information
    sources = []

    for chunk in chunks:

        sources.append({

            "section": chunk["section"],

            "page": chunk["page_number"],

            "score": round(chunk["score"], 4),

            "chunk_id": chunk["chunk_id"]

        })

    return {

        "question": request.question,

        "answer": answer,

        "sources": sources

    }