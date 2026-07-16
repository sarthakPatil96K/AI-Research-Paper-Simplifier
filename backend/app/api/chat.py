from fastapi import APIRouter

from app.schemas.chat_schema import ChatRequest
from app.core.container import container

router = APIRouter()


@router.post("/chat")
def chat(request: ChatRequest):

    query_embedding = (
        container.embedding_service.embed_query(
            request.question
        )
    )

    chunks = (
        container.vector_service.search(
            request.paper_id,
            query_embedding,
            request.top_k
        )
    )

    context = "\n\n".join(
        [
            f"[{c['section']}]\n{c['text']}"
            for c in chunks
        ]
    )

    answer = (
        container.llm_service.answer(
            request.question,
            context
        )
    )

    return {

        "question": request.question,

        "answer": answer,

        "sources": [

            {
                "section": c["section"],
                "score": c["score"]
            }

            for c in chunks

        ]
    }