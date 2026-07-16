from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer(
    "BAAI/bge-small-en-v1.5"
)

texts = [
    "Deep learning improves medical diagnosis.",
    "Neural networks help detect diseases.",
    "The weather is sunny today."
]

embeddings = model.encode(
    texts,
    normalize_embeddings=True
)

print(
    cosine_similarity(
        [embeddings[0]],
        [embeddings[1]]
    )
)

print(
    cosine_similarity(
        [embeddings[0]],
        [embeddings[2]]
    )
)