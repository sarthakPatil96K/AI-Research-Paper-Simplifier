from app.llm.gemini_provider import GeminiProvider


class LLMService:

    def __init__(self):

        self.provider = GeminiProvider()

    def answer(
        self,
        question,
        context
    ):

        return self.provider.generate(
            question,
            context
        )