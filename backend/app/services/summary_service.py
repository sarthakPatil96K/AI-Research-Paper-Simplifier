import json
import os
from datetime import datetime


class SummaryService:

    SUMMARY_DIR = "storage/summaries"

    def __init__(self, llm_service):
        self.llm_service = llm_service
        os.makedirs(self.SUMMARY_DIR, exist_ok=True)

    def generate_summary(self, paper_id, chunks):

        # --- Build context from ALL chunks, not just a few sections ---
        context_parts = []
        for chunk in chunks:
            text = chunk.get("text", "").strip()
            if not text:
                continue
            section = chunk.get("section") or "Unknown"
            context_parts.append(f"\nSection: {section}\n{text}\n")

        context = "".join(context_parts)

        if not context.strip():
            summary = {"error": "No text available to summarize."}
        else:
            # --- Use the dedicated structured-summary method ---
            provider = self.llm_service.provider

            if hasattr(provider, "generate_summary"):
                summary = provider.generate_summary(context)
            else:
                # Fallback if generate_summary() isn't defined yet
                summary = provider.generate(
                    question=(
                        "Return ONLY a JSON object with keys: title, objective, "
                        "problem, methodology, datasets, architecture, results, "
                        "limitations, future_work, keywords. "
                        "Do not include any other text or markdown fences."
                    ),
                    context=context,
                )

        filepath = os.path.join(self.SUMMARY_DIR, f"{paper_id}.json")
        with open(filepath, "w") as f:
            json.dump(
                {
                    "paper_id": paper_id,
                    "summary": summary,
                    "generated_at": str(datetime.now()),
                },
                f,
                indent=4,
            )

        return summary

    def load_summary(self, paper_id):
        filepath = os.path.join(self.SUMMARY_DIR, f"{paper_id}.json")
        if not os.path.exists(filepath):
            return None
        with open(filepath) as f:
            return json.load(f)