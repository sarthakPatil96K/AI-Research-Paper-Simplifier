import uuid

from app.services.document_parser import DocumentParser
from app.services.section_chunker import SectionChunker


class PaperService:

    def __init__(
        self,
        embedding_service,
        vector_service,
        summary_service,
        bm25_service
    ):
        self.embedding_service = embedding_service
        self.vector_service = vector_service
        self.bm25_service = bm25_service
        self.summary_service = summary_service

    def process_pdf(self, file_path, metadata=None):
        print("=" * 60)
        print("🚀 PAPER SERVICE STARTED")
        print("=" * 60)

        paper_id = str(uuid.uuid4())
        print(f"[1] Paper ID: {paper_id}")

        document = DocumentParser.parse(file_path)
        print(f"[2] PDF Parsed Successfully")
        print(f"    Pages: {len(document['pages'])}")

        chunks = SectionChunker.create_chunks(
            document=document,
            paper_id=paper_id
        )
        print(f"[3] Chunks Created: {len(chunks)}")

        if len(chunks) == 0:
            raise Exception("No chunks could be created from the document.")

        print(f"    First Chunk Section: {chunks[0]['section']}")
        print(f"    First Chunk Words: {chunks[0]['word_count']}")

        print("[4] Generating Embeddings...")
        embeddings = self.embedding_service.generate_embeddings(chunks)
        print(f"[5] Embeddings Generated: {len(embeddings)}")

        if embeddings:
            print(f"    Embedding Dimension: {len(embeddings[0]['embedding'])}")

        print("[6] Calling VectorService.create_index()")
        self.vector_service.create_index(paper_id, embeddings)
        self.bm25_service.create_index(paper_id, chunks)

        print("[8] Generating Summary...")
        summary = self.summary_service.generate_summary(paper_id, chunks)
        print("[9] Summary Generated")
        print("[7] Returned from create_index()")

        print("=" * 60)
        print("✅ PAPER PROCESSING COMPLETED")
        print("=" * 60)

        paper_title = document["metadata"].get("title", "")
        if not paper_title or not paper_title.strip():
            first_chunk_text = chunks[0].get("text", "") if chunks else ""
            first_line = first_chunk_text.split("\n")[0][:100]
            document["metadata"]["title"] = first_line.strip() if first_line else "Untitled Paper"

        return {
            "paper_id": paper_id,
            "paper": document["metadata"],
            "pages": len(document["pages"]),
            "total_chunks": len(chunks),
            "summary": summary,
            "embedding_dimension": len(embeddings[0]["embedding"]) if embeddings else 0,
            "first_chunk": {
                "section": chunks[0]["section"],
                "page": chunks[0]["page_number"],
                "words": chunks[0]["word_count"]
            }
        }