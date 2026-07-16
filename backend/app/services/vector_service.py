import faiss
import numpy as np
import os
import pickle


class VectorService:

    INDEX_DIR = "vector_db/indexes"
    META_DIR = "vector_db/metadata"

    def __init__(self):

        os.makedirs(self.INDEX_DIR, exist_ok=True)
        os.makedirs(self.META_DIR, exist_ok=True)

    def create_index(self, paper_id, embeddings):

        vectors = np.array(
            [e["embedding"] for e in embeddings],
            dtype="float32"
        )

        dimension = vectors.shape[1]

        index = faiss.IndexFlatIP(dimension)

        index.add(vectors)

        index_path = os.path.join(
            self.INDEX_DIR,
            f"{paper_id}.index"
        )

        faiss.write_index(index, index_path)

        metadata = []

        for item in embeddings:

            metadata.append({

            "paper_id": item["paper_id"],

            "chunk_id": item["chunk_id"],

            "section": item["section"],

            "page_number": item["page_number"],

            "word_count": item["word_count"],

            "text": item["text"]

        })

        metadata_path = os.path.join(
            self.META_DIR,
            f"{paper_id}.pkl"
        )

        with open(metadata_path, "wb") as f:

            pickle.dump(metadata, f)

        return index_path
    
    def search(
        self,
        paper_id,
        query_embedding,
        top_k=5
    ):

        index_path = os.path.join(
            self.INDEX_DIR,
            f"{paper_id}.index"
        )

        metadata_path = os.path.join(
            self.META_DIR,
            f"{paper_id}.pkl"
        )

        index = faiss.read_index(index_path)

        with open(metadata_path, "rb") as f:

            metadata = pickle.load(f)

        query = np.array(
            [query_embedding],
            dtype="float32"
        )

        scores, ids = index.search(query, top_k)

        results = []

        for score, idx in zip(scores[0], ids[0]):

            if idx == -1:
                continue

            results.append({

                "score": float(score),

                **metadata[idx]

            })

        return results