import os

import google.generativeai as genai
from dotenv import load_dotenv

from app.llm.base import BaseLLM

load_dotenv()


class GeminiProvider(BaseLLM):

    def __init__(self):

        genai.configure(
            api_key=os.getenv("GEMINI_API_KEY")
        )

        self.model = genai.GenerativeModel(
            "gemini-3.5-flash"
        )

    def generate(
        self,
        question,
        context
    ):

        prompt = f"""
You are an AI Research Assistant.

Use ONLY the provided context.

If the answer is not present, reply:

"I couldn't find this information in the uploaded paper."

Context:

{context}

Question:

{question}

Answer:
"""

        response = self.model.generate_content(
            prompt
        )

        return response.text