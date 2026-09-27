from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService
from app.services.paper_service import PaperService
from app.services.summary_service import SummaryService

from app.llm.llm_service import LLMService
from app.services.bm25_service import BM25Service

from app.services.hybrid_search_service import HybridSearchService

...


class ServiceContainer:

    def __init__(self):

        print("Loading Embedding Model...")

        # Embedding Service
        self.embedding_service = EmbeddingService()

        print("Embedding Model Loaded")

        # LLM Service
        self.llm_service = LLMService()

        # Vector Service
        self.vector_service = VectorService()

        # Summary Service
        self.summary_service = SummaryService(
            self.llm_service
        )
        self.bm25_service = BM25Service()
        self.hybrid_search_service = HybridSearchService(
            self.vector_service,
            self.bm25_service
        )

        # Paper Service
        self.paper_service = PaperService(
            embedding_service=self.embedding_service,
            vector_service=self.vector_service,
            summary_service=self.summary_service,
            bm25_service=self.bm25_service
        )


container = ServiceContainer()