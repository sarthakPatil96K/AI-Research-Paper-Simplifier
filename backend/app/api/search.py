from fastapi import APIRouter

from app.schemas.search_schema import SearchRequest
from app.core.container import container

router = APIRouter()


@router.post("/search")
def semantic_search(request: SearchRequest):

    query_embedding = (
        container.embedding_service.embed_query(
            request.question
        )
    )

    results = container.hybrid_search_service.search(
        paper_id=request.paper_id,
        embedding=query_embedding,
        query=request.question,
        top_k=request.top_k
    )

    return {
        "question": request.question,
        "results": results
    }