class HybridSearchService:

    # Weighting: semantic vs lexical
    SEMANTIC_WEIGHT = 0.8
    BM25_WEIGHT = 0.2

    # Minimum raw cosine similarity to consider a hit relevant
    MIN_SEMANTIC = 0.30

    def __init__(self, vector_service, bm25_service):
        self.vector_service = vector_service
        self.bm25_service = bm25_service

    @staticmethod
    def normalize(values):
        if not values:
            return []
        mn = min(values)
        mx = max(values)
        if mx - mn < 1e-9:
            return [1.0 for _ in values]
        return [(v - mn) / (mx - mn) for v in values]

    def search(self, paper_id, embedding, query, top_k=5):

        # --- Retrieve candidates from each source ---
        semantic = self.vector_service.search(
            paper_id, embedding, top_k=top_k * 3
        )
        lexical = self.bm25_service.search(
            paper_id, query, top_k=top_k * 3
        )

        # --- Drop weak semantic hits up front ---
        semantic = [c for c in semantic if c["score"] >= self.MIN_SEMANTIC]

        if not semantic and not lexical:
            return []

        semantic_scores = self.normalize([c["score"] for c in semantic])
        bm25_scores = self.normalize([c["bm25_score"] for c in lexical])

        fused = {}

        # --- Semantic side ---
        for chunk, norm in zip(semantic, semantic_scores):
            fused[chunk["chunk_id"]] = {
                **chunk,
                "raw_semantic_score": chunk["score"],
                "raw_bm25_score": 0.0,
                "semantic_score": norm,
                "bm25_score": 0.0,
                "final_score": norm * self.SEMANTIC_WEIGHT,
            }

        # --- BM25 side (merge or add) ---
        for chunk, norm in zip(lexical, bm25_scores):
            cid = chunk["chunk_id"]

            if cid in fused:
                fused[cid]["raw_bm25_score"] = chunk["bm25_score"]
                fused[cid]["bm25_score"] = norm
                fused[cid]["final_score"] += norm * self.BM25_WEIGHT
            else:
                fused[cid] = {
                    **chunk,
                    "score": 0.0,
                    "raw_semantic_score": 0.0,
                    "raw_bm25_score": chunk["bm25_score"],
                    "semantic_score": 0.0,
                    "bm25_score": norm,
                    "final_score": norm * self.BM25_WEIGHT,
                }

        results = sorted(
            fused.values(),
            key=lambda x: x["final_score"],
            reverse=True,
        )

        return results[:top_k]