from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.services.paper_service import PaperService
from app.llm.llm_service import LLMService

class ServiceContainer:

    def __init__(self):

        print("Loading Embedding Model...")

        self.embedding_service = EmbeddingService()

        print("Embedding Model Loaded")
        self.llm_service = LLMService()
        self.vector_service = VectorService()

        self.paper_service = PaperService(
            embedding_service=self.embedding_service,
            vector_service=self.vector_service
        )


container = ServiceContainer()