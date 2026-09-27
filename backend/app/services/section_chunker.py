import re
from typing import Dict, List

from app.services.document_parser import DocumentParser


class SectionChunker:

    MAX_WORDS = 180
    OVERLAP = 50

    MAJOR_HEADINGS = {
        "ABSTRACT",
        "INTRODUCTION",
        "RELATED WORK",
        "LITERATURE REVIEW",
        "BACKGROUND",
        "METHOD",
        "METHODS",
        "METHODOLOGY",
        "PROPOSED METHOD",
        "EXPERIMENTS",
        "EXPERIMENTAL SETUP",
        "RESULTS",
        "DISCUSSION",
        "CONCLUSION",
        "CONCLUSIONS",
        "LIMITATIONS",
        "ETHICAL CONSIDERATIONS",
        "FUTURE WORK",
    }

    # ------------------------------------------------------------------
    # Heading / section recognition
    # ------------------------------------------------------------------
    @staticmethod
    def _matches_known_heading(upper: str) -> bool:
        if upper in SectionChunker.MAJOR_HEADINGS:
            return True
        compact = re.sub(r"\s+", "", upper)
        for h in SectionChunker.MAJOR_HEADINGS:
            if h.replace(" ", "") == compact:
                return True
        return False

    @staticmethod
    def is_new_section(title: str) -> bool:
        title = DocumentParser.normalize_text(title).strip(" .:")
        if not title:
            return False

        # Numbered heading ("1 Introduction", "3.1 Foo")
        if re.match(r"^\d+(\.\d+)*\s+\S", title):
            return True

        return SectionChunker._matches_known_heading(title.upper())

    @staticmethod
    def canonical_label(title: str) -> str:
        """
        Produce a clean label to store as `section`:
        - Known heading → Title Case ("Abstract", "Related Work")
        - Numbered heading → cleaned original text
        """
        norm = DocumentParser.normalize_text(title).strip(" .:")
        upper = norm.upper()

        # Exact known match
        if upper in SectionChunker.MAJOR_HEADINGS:
            return upper.title()

        # Glued letters match
        compact = re.sub(r"\s+", "", upper)
        for h in SectionChunker.MAJOR_HEADINGS:
            if h.replace(" ", "") == compact:
                return h.title()

        return norm

    # ------------------------------------------------------------------
    # Chunking
    # ------------------------------------------------------------------
    @staticmethod
    def create_chunks(document: Dict, paper_id: str):

        chunks: List[Dict] = []

        current_section = "Unknown"
        chunk_id = 1
        buffer: List[str] = []
        page_number = 1
        paragraph_number = 0

        def flush():
            nonlocal buffer, chunk_id
            if not buffer:
                return
            chunks.append(
                {
                    "paper_id": paper_id,
                    "chunk_id": chunk_id,
                    "page_number": page_number,
                    "section": current_section,
                    "paragraph_number": paragraph_number,
                    "word_count": len(buffer),
                    "text": " ".join(buffer),
                }
            )
            chunk_id += 1
            if len(buffer) > SectionChunker.OVERLAP:
                buffer = buffer[-SectionChunker.OVERLAP:]
            else:
                buffer = []

        for page in document["pages"]:

            page_number = page["page"]

            for block in page["blocks"]:

                if block["type"] == "heading":

                    title = block["text"]

                    if SectionChunker.is_new_section(title):

                        flush()
                        # Use the canonical label so downstream
                        # code sees "Abstract", not "A B S T R A C T"
                        current_section = SectionChunker.canonical_label(title)
                        paragraph_number = 0
                        buffer = []

                    else:
                        # Small inline heading → treat as paragraph text
                        buffer.extend(title.split())

                    continue

                paragraph_number += 1
                words = block["text"].split()

                while words:

                    remaining = SectionChunker.MAX_WORDS - len(buffer)

                    if len(words) <= remaining:
                        buffer.extend(words)
                        words = []
                    else:
                        buffer.extend(words[:remaining])
                        flush()
                        words = words[remaining:]

        flush()

        print("\n========== CHUNKS ==========")
        for chunk in chunks:
            print(
                f"Chunk {chunk['chunk_id']:02d} | "
                f"{chunk['section']} | "
                f"Page {chunk['page_number']} | "
                f"{chunk['word_count']} words"
            )

        return chunks