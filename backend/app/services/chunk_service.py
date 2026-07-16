import re


class ChunkService:

    SECTION_HEADINGS = [
        "Abstract",
        "Introduction",
        "Related Work",
        "Literature Review",
        "Background",
        "Methodology",
        "Materials and Methods",
        "Proposed Method",
        "Experiments",
        "Experimental Results",
        "Results",
        "Discussion",
        "Conclusion",
        "Future Work",
        "References"
    ]

    @staticmethod
    def clean_text(text: str):

        # remove multiple spaces
        text = re.sub(r"[ \t]+", " ", text)

        # remove multiple blank lines
        text = re.sub(r"\n{3,}", "\n\n", text)

        # remove page numbers
        text = re.sub(r"\n\s*\d+\s*\n", "\n", text)

        return text.strip()
    
    @staticmethod
    def extract_sections(text):

        positions = []

        for heading in ChunkService.SECTION_HEADINGS:

            match = re.search(
                rf"\b{re.escape(heading)}\b",
                text,
                re.IGNORECASE
            )

            if match:

                positions.append(
                    (
                        heading,
                        match.start()
                    )
                )

        positions.sort(key=lambda x: x[1])

        sections = {}

        for i in range(len(positions)):

            heading, start = positions[i]

            if i < len(positions) - 1:

                end = positions[i + 1][1]

            else:

                end = len(text)

            sections[heading] = text[start:end].strip()

        return sections
        
    @staticmethod
    def create_chunks(
            sections,
            chunk_size=450,
            overlap=50):

        chunks = []

        chunk_id = 1

        for section_name, content in sections.items():

            words = content.split()

            start = 0

            while start < len(words):

                end = start + chunk_size

                chunk_words = words[start:end]

                chunks.append({

                    "chunk_id": chunk_id,

                    "paper_id": None,

                    "section": section_name,

                    "page_number": 1,        # We'll improve this later

                    "word_count": len(chunk_words),

                    "text": " ".join(chunk_words)

                })
                chunk_id += 1

                start += chunk_size - overlap

        return chunks