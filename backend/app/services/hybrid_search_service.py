class HybridSearchService:

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

        return [
            (v - mn) / (mx - mn)
            for v in values
        ]

    def search(
        self,
        paper_id,
        embedding,
        query,
        top_k=5
    ):

        semantic = self.vector_service.search(
            paper_id,
            embedding,
            top_k=top_k * 3
        )

        lexical = self.bm25_service.search(
            paper_id,
            query,
            top_k=top_k * 3
        )

        print("\n========== SEMANTIC ==========")
        for i, c in enumerate(semantic, 1):
            print(f"{i}. {c['section']} | {c['score']:.4f}")

        print("\n========== BM25 ==========")
        for i, c in enumerate(lexical, 1):
            print(f"{i}. {c['section']} | {c['bm25_score']:.4f}")

        semantic_scores = self.normalize(
            [c["score"] for c in semantic]
        )

        bm25_scores = self.normalize(
            [c["bm25_score"] for c in lexical]
        )

        fused = {}

        # Semantic (80%)
        for chunk, score in zip(semantic, semantic_scores):

            fused[chunk["chunk_id"]] = {
                **chunk,
                "semantic_score": score,
                "bm25_score": 0.0,
                "final_score": score * 0.8
            }

        # BM25 (20%)
        for chunk, score in zip(lexical, bm25_scores):

            cid = chunk["chunk_id"]

            if cid in fused:

                fused[cid]["bm25_score"] = score
                fused[cid]["final_score"] += score * 0.2

            else:

                fused[cid] = {
                    **chunk,
                    "score": 0,
                    "semantic_score": 0,
                    "bm25_score": score,
                    "final_score": score * 0.2
                }

        results = sorted(
            fused.values(),
            key=lambda x: x["final_score"],
            reverse=True
        )

        print("\n========== HYBRID ==========")

        for i, c in enumerate(results[:top_k], 1):

            print(
                f"{i}. {c['section']} | "
                f"Semantic={c['semantic_score']:.3f} | "
                f"BM25={c['bm25_score']:.3f} | "
                f"Final={c['final_score']:.3f}"
            )

        return results[:top_k]