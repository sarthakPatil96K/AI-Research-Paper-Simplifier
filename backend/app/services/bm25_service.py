import os
import pickle

from rank_bm25 import BM25Okapi


class BM25Service:

    BM25_DIR = "vector_db/bm25"

    def __init__(self):

        os.makedirs(self.BM25_DIR, exist_ok=True)

    def create_index(self, paper_id, chunks):

        corpus = [
            chunk["text"].lower().split()
            for chunk in chunks
        ]

        bm25 = BM25Okapi(corpus)

        data = {
            "bm25": bm25,
            "chunks": chunks
        }

        with open(
            os.path.join(
                self.BM25_DIR,
                f"{paper_id}.pkl"
            ),
            "wb"
        ) as f:

            pickle.dump(data, f)

    def search(
        self,
        paper_id,
        query,
        top_k=5
    ):

        filepath = os.path.join(
            self.BM25_DIR,
            f"{paper_id}.pkl"
        )

        if not os.path.exists(filepath):

            return []

        with open(filepath, "rb") as f:

            data = pickle.load(f)

        bm25 = data["bm25"]

        chunks = data["chunks"]

        scores = bm25.get_scores(
            query.lower().split()
        )

        ranked = sorted(
            zip(chunks, scores),
            key=lambda x: x[1],
            reverse=True
        )

        results = []

        for chunk, score in ranked[:top_k]:

            result = chunk.copy()

            result["bm25_score"] = float(score)

            results.append(result)

        return results