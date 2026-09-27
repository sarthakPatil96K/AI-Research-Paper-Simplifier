from fastapi import APIRouter, HTTPException

from app.core.container import container

router = APIRouter()


@router.get("/paper/{paper_id}/summary")
def get_summary(paper_id: str):

    summary = container.summary_service.load_summary(
        paper_id
    )

    if summary is None:

        raise HTTPException(
            status_code=404,
            detail="Summary not found."
        )

    return summary