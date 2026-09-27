import json
import os
import uuid
from datetime import datetime

from app.services.document_parser import DocumentParser
from app.services.section_chunker import SectionChunker


class PaperService:

    def __init__(
        self,
        embedding_service,
        vector_service,
        summary_service,
        bm25_service,
    ):
        self.embedding_service = embedding_service
        self.vector_service = vector_service
        self.bm25_service = bm25_service
        self.summary_service = summary_service

    def process_pdf(self, file_path, metadata=None):
        print("=" * 60)
        print("🚀 PAPER SERVICE STARTED")
        print("=" * 60)

        paper_id = str(uuid.uuid4())
        print(f"[1] Paper ID: {paper_id}")

        document = DocumentParser.parse(file_path)
        print("[2] PDF Parsed Successfully")
        print(f"    Pages: {len(document['pages'])}")

        chunks = SectionChunker.create_chunks(
            document=document,
            paper_id=paper_id,
        )
        print(f"[3] Chunks Created: {len(chunks)}")

        if len(chunks) == 0:
            raise Exception("No chunks could be created from the document.")

        print(f"    First Chunk Section: {chunks[0]['section']}")
        print(f"    First Chunk Words: {chunks[0]['word_count']}")

        # ---------- Embeddings ----------
        print("[4] Generating Embeddings...")
        embeddings = self.embedding_service.generate_embeddings(chunks)
        print(f"[5] Embeddings Generated: {len(embeddings)}")

        if embeddings:
            print(f"    Embedding Dimension: {len(embeddings[0]['embedding'])}")

        # ---------- Vector + BM25 indexes ----------
        print("[6] Calling VectorService.create_index()")
        self.vector_service.create_index(paper_id, embeddings)
        self.bm25_service.create_index(paper_id, chunks)

        # ---------- Summary (needed for title fallback) ----------
        print("[8] Generating Summary...")
        summary = self.summary_service.generate_summary(paper_id, chunks)
        print("[9] Summary Generated")
        print("[7] Returned from create_index()")

        # =========================================================
        # Build final metadata BEFORE writing the sidecar file
        # =========================================================
        paper_meta = dict(document.get("metadata") or {})

        # ----- Title cleanup -----
        title = (paper_meta.get("title") or "").strip()
        # PDFMaker / Word often prefixes with "Title:" — strip it
        if title.lower().startswith("title:"):
            title = title[6:].strip()

        # Fallback 1: Gemini-extracted title from the summary
        if not title and isinstance(summary, dict):
            title = (summary.get("title") or "").strip()

        # Fallback 2: first meaningful line of the first chunk
        if not title:
            for ch in chunks:
                text = (ch.get("text") or "").strip()
                if not text:
                    continue
                first_line = text.split("\n")[0].strip()
                if len(first_line) > 8:
                    title = first_line[:200]
                    break

        paper_meta["title"] = title or "Untitled"

        # ----- Author cleanup -----
        author = (paper_meta.get("author") or "").strip()
        junk_authors = {
            "", "unknown", "untitled", "microsoft word", "admin",
            "user", "owner", "administrator",
        }
        if author.lower() in junk_authors:
            author = self._guess_author(chunks) or "Unknown"
        paper_meta["author"] = author

        # =========================================================
        # Write the metadata sidecar (now populated)
        # =========================================================
        metadata_dir = "vector_db/metadata"
        os.makedirs(metadata_dir, exist_ok=True)
        with open(os.path.join(metadata_dir, f"{paper_id}.json"), "w") as f:
            json.dump(
                {
                    "paper_id": paper_id,
                    "metadata": paper_meta,
                    "page_count": len(document["pages"]),
                    "total_chunks": len(chunks),
                    "uploaded_at": str(datetime.now()),
                },
                f,
                indent=4,
            )

        print("=" * 60)
        print("✅ PAPER PROCESSING COMPLETED")
        print("=" * 60)

        return {
            "paper_id": paper_id,
            "paper": paper_meta,
            "pages": len(document["pages"]),
            "total_chunks": len(chunks),
            "summary": summary,
            "embedding_dimension": len(embeddings[0]["embedding"]) if embeddings else 0,
            "first_chunk": {
                "section": chunks[0]["section"],
                "page": chunks[0]["page_number"],
                "words": chunks[0]["word_count"],
            },
        }

    # ------------------------------------------------------------------
    # Heuristic author guesser
    # ------------------------------------------------------------------
    @staticmethod
    def _guess_author(chunks) -> str | None:
        """
        Look at the head of the first chunk for a plausible author line.
        Handles:
          - "Author: Jane Doe"
          - "By Jane Doe"
          - A short line "Jane Doe" right after the title
        """
        import re

        if not chunks:
            return None

        head = (chunks[0].get("text") or "")[:600]
        lines = [l.strip() for l in head.split("\n") if l.strip()]

        # Pattern 1: explicit label
        for line in lines[:12]:
            m = re.match(
                r"^(?:authors?|by)\s*[:\-]?\s*(.+)$",
                line,
                re.IGNORECASE,
            )
            if m:
                cand = m.group(1).strip(" ,;:")
                if 2 <= len(cand) <= 100:
                    return cand

        # Pattern 2: "Firstname Lastname" — 2-4 capitalised words
        name_re = re.compile(
            r"^([A-Z][a-zA-Z.\-']+(?:\s+[A-Z][a-zA-Z.\-']+){1,3})$"
        )
        skip = {"abstract", "introduction", "conclusion", "keywords"}
        for line in lines[:10]:
            if line.lower() in skip:
                continue
            if 2 <= len(line) <= 60 and name_re.match(line):
                return line

        return None