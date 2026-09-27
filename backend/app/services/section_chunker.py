from typing import List, Dict
import re


class SectionChunker:

    MAX_WORDS = 180
    OVERLAP = 50

    MAJOR_HEADINGS = {
        "ABSTRACT",
        "INTRODUCTION",
        "RELATED WORK",
        "BACKGROUND",
        "METHOD",
        "METHODS",
        "RESULTS",
        "DISCUSSION",
        "CONCLUSION",
        "LIMITATIONS",
        "ETHICAL CONSIDERATIONS"
    }

    @staticmethod
    def is_new_section(title: str):

        title = title.strip()

        # Numbered headings
        if re.match(r"^\d+(\.\d+)*\s+", title):
            return True

        if title.upper() in SectionChunker.MAJOR_HEADINGS:
            return True

        return False

    @staticmethod
    def create_chunks(document: Dict, paper_id: str):

        chunks = []

        current_section = "Unknown"

        chunk_id = 1

        buffer = []

        page_number = 1

        paragraph_number = 0

        def flush():

            nonlocal buffer
            nonlocal chunk_id

            if not buffer:
                return

            chunks.append({

                "paper_id": paper_id,

                "chunk_id": chunk_id,

                "page_number": page_number,

                "section": current_section,

                "paragraph_number": paragraph_number,

                "word_count": len(buffer),

                "text": " ".join(buffer)

            })

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

                        current_section = title

                        paragraph_number = 0

                        buffer = []

                    else:

                        # Small heading → keep inside paragraph
                        buffer.extend(title.split())

                    continue

                paragraph_number += 1

                words = block["text"].split()

                while words:

                    remaining = (
                        SectionChunker.MAX_WORDS
                        - len(buffer)
                    )

                    if len(words) <= remaining:

                        buffer.extend(words)

                        words = []

                    else:

                        buffer.extend(
                            words[:remaining]
                        )

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