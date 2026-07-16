from app.services.embedding_service import EmbeddingService

service = EmbeddingService()

embedding = service.generate_embedding(
    "Artificial Intelligence is transforming healthcare."
)

print(type(embedding))

print(len(embedding))

print(embedding[:10])