from sentence_transformers import SentenceTransformer
import numpy as np


class EmbeddingService:
    """
    Handles loading the embedding model
    and converting text into vectors.
    """

    def __init__(self):

        self.model = SentenceTransformer(
            "BAAI/bge-small-en-v1.5"
        )

    def generate_embedding(self, text):

        embedding = self.model.encode(
            text,
            normalize_embeddings=True
        )

        return embedding.tolist()

    def generate_embeddings(self, chunks):

        embeddings = []

        for chunk in chunks:

            vector = self.generate_embedding(
                chunk["text"]
            )

            embeddings.append({

            "paper_id": chunk["paper_id"],

            "chunk_id": chunk["chunk_id"],

            "section": chunk["section"],

            "page_number": chunk["page_number"],

            "word_count": chunk["word_count"],

            "text": chunk["text"],

            "embedding": vector

        })

        return embeddings
    def embed_query(self, query: str):

        return self.model.encode(
            query,
            normalize_embeddings=True
        ).tolist()