import os
import json
import re
import time

from google import genai
from google.genai import errors, types
from dotenv import load_dotenv

from app.llm.base import BaseLLM

load_dotenv()


class GeminiProvider(BaseLLM):
    def __init__(self):
        self.client = genai.Client()
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
        self.max_retries = 4
        self.base_delay = 2.0

    @staticmethod
    def _strip_code_fences(text: str) -> str:
        cleaned = (text or "").strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        return cleaned.strip()

    def _call_with_retry(self, prompt: str, json_mode: bool = False):
        config = None
        if json_mode:
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
            )

        retryable = {429, 500, 502, 503, 504}
        last_error = None

        for attempt in range(self.max_retries):
            try:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=config,
                )
                return response.text.strip() if response.text else ""
            except errors.APIError as e:
                code = getattr(e, "code", None)
                if code in retryable and attempt < self.max_retries - 1:
                    delay = self.base_delay * (2 ** attempt)
                    print(f"[Gemini] {code} retry {attempt+1}/{self.max_retries} in {delay}s")
                    time.sleep(delay)
                    last_error = e
                    continue
                raise
        if last_error:
            raise last_error

    def generate(self, question, context):
        prompt = f"""
You are an AI Research Paper Assistant.
Answer ONLY using the supplied research paper context.
If the answer is not in the context, reply exactly:
"I couldn't find this information in the uploaded paper."

RESEARCH PAPER CONTEXT
{context}

USER QUESTION
{question}
"""
        try:
            return self._call_with_retry(prompt) or "The model returned an empty response."
        except errors.APIError as e:
            code = getattr(e, "code", None)
            if code == 429:
                return "The Gemini API quota has been exceeded. Please wait a minute and try again."
            if code == 503:
                return "Gemini is temporarily overloaded. Please try again shortly."
            return f"LLM API Error: {str(e)}"
        except Exception as e:
            return f"LLM Error: {str(e)}"

    def generate_summary(self, context: str) -> dict:
        prompt = f"""
You are an AI Research Paper Assistant.
Read the paper context and return ONLY a valid JSON object with these keys:
{{
  "title": "",
  "objective": "",
  "problem": "",
  "methodology": "",
  "datasets": "",
  "architecture": "",
  "results": "",
  "limitations": "",
  "future_work": "",
  "keywords": []
}}

Rules:
- No text outside the JSON.
- No markdown fences.
- If a field is missing, write "Not specified".

PAPER CONTEXT:
{context}
"""
        try:
            raw = self._call_with_retry(prompt, json_mode=True)
            cleaned = self._strip_code_fences(raw)
            parsed = json.loads(cleaned)
            # If the model returned a "message" (conversational fallback),
            # treat it as a failure instead of a summary.
            if isinstance(parsed, dict) and "message" in parsed and len(parsed) == 1:
                return {"error": f"Model returned chat fallback: {parsed['message']}"}
            return parsed
        except json.JSONDecodeError:
            return {"raw": raw}
        except errors.APIError as e:
            code = getattr(e, "code", None)
            if code == 429:
                return {"error": "Gemini API quota exceeded. Try again shortly."}
            if code == 503:
                return {"error": "Gemini is temporarily overloaded. Please try again shortly."}
            return {"error": f"LLM API Error: {str(e)}"}
        except Exception as e:
            return {"error": f"LLM Error: {str(e)}"}