import os
import pickle
import re
import unicodedata

from rank_bm25 import BM25Okapi


# Common English stopwords — remove to reduce noise in BM25
_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "has", "he", "in", "is", "it", "its", "of", "on", "or", "that",
    "the", "to", "was", "were", "will", "with", "this", "these",
    "those", "we", "you", "i", "they", "them", "their", "our", "us",
    "but", "if", "then", "than", "so", "not", "no", "do", "does",
    "did", "been", "being", "have", "had", "can", "could", "would",
    "should", "may", "might", "must", "shall",
}


def normalize_text(text: str) -> str:
    """
    - Decompose ligatures (ﬁ → fi) and accents
    - Lowercase
    - Remove non-alphanumeric characters (keep spaces)
    """
    if not text:
        return ""
    # NFKD decomposes ﬁ, ﬂ, é, etc. into base + combining marks
    text = unicodedata.normalize("NFKD", text)
    # Drop combining marks (the accents)
    text = "".join(c for c in text if not unicodedata.combining(c))
    # Lowercase and keep only letters/digits/spaces
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    # Collapse multiple spaces
    text = re.sub(r"\s+", " ", text).strip()
    return text


def tokenize(text: str, remove_stopwords: bool = False) -> list[str]:
    tokens = normalize_text(text).split()
    if remove_stopwords:
        tokens = [t for t in tokens if t not in _STOPWORDS and len(t) > 1]
    return tokens


class BM25Service:

    BM25_DIR = "vector_db/bm25"

    def __init__(self):
        os.makedirs(self.BM25_DIR, exist_ok=True)

    def create_index(self, paper_id, chunks):
        corpus = [tokenize(chunk["text"]) for chunk in chunks]
        bm25 = BM25Okapi(corpus)

        data = {
            "bm25": bm25,
            "chunks": chunks,
        }

        filepath = os.path.join(self.BM25_DIR, f"{paper_id}.pkl")
        with open(filepath, "wb") as f:
            pickle.dump(data, f)

    def search(self, paper_id, query, top_k=5):
        filepath = os.path.join(self.BM25_DIR, f"{paper_id}.pkl")
        if not os.path.exists(filepath):
            return []

        with open(filepath, "rb") as f:
            data = pickle.load(f)

        bm25 = data["bm25"]
        chunks = data["chunks"]

        # Tokenize the query the same way as the corpus
        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scores = bm25.get_scores(query_tokens)

        ranked = sorted(
            zip(chunks, scores),
            key=lambda x: x[1],
            reverse=True,
        )

        results = []
        for chunk, score in ranked[:top_k]:
            result = chunk.copy()
            result["bm25_score"] = float(score)
            results.append(result)

        return results