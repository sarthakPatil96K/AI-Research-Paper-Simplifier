from pydantic import BaseModel


class ChatRequest(BaseModel):

    paper_id: str

    question: str

    top_k: int = 5