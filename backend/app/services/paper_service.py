import uuid

from app.services.pdf_service import PDFService
from app.services.chunk_service import ChunkService
from app.services.embedding_service import EmbeddingService
from app.services.vector_service import VectorService


class PaperService:

    def __init__(
        self,
        embedding_service,
        vector_service
    ):

        self.embedding_service = embedding_service

        self.vector_service = vector_service

    def process_pdf(
        self,
        file_path,
        metadata
    ):

        paper_id = str(uuid.uuid4())

        text_data = PDFService.extract_text_from_pdf(
            file_path
        )

        clean_text = ChunkService.clean_text(
            text_data["full_text"]
        )

        sections = ChunkService.extract_sections(
            clean_text
        )

        chunks = ChunkService.create_chunks(
            sections
        )
        for chunk in chunks:
            chunk["paper_id"] = paper_id
        embeddings = self.embedding_service.generate_embeddings(
            chunks
        )

        self.vector_service.create_index(
            paper_id,
            embeddings
        )

        return {

            "paper_id": paper_id,

            "paper": metadata,

            "sections": list(sections.keys()),

            "total_chunks": len(chunks),

            "embedding_dimension": len(
                embeddings[0]["embedding"]
            )

        }