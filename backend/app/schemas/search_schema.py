from pydantic import BaseModel


class SearchRequest(BaseModel):
    paper_id: str
    question: str
    top_k: int = 5