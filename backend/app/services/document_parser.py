import re
import unicodedata

import pymupdf as fitz


class DocumentParser:

    HEADING_PATTERNS = [
        r"^\d+\.?\s+[A-Z].*",
        r"^[IVXLC]+\.\s+.*",
        r"^(ABSTRACT|INTRODUCTION|RELATED WORK|LITERATURE REVIEW|"
        r"BACKGROUND|METHODOLOGY|METHODS|PROPOSED METHOD|EXPERIMENTS|"
        r"RESULTS|DISCUSSION|CONCLUSION|FUTURE WORK|REFERENCES)$",
    ]

    # Canonical set of section names we recognize
    KNOWN_HEADINGS = {
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
        "REFERENCES",
        "ACKNOWLEDGEMENT",
        "ACKNOWLEDGEMENTS",
        "APPENDIX",
    }

    # ------------------------------------------------------------------
    # Text normalization
    # ------------------------------------------------------------------
    @staticmethod
    def normalize_text(text: str) -> str:
        """
        - Fix ligatures (ﬁ → fi) and accents
        - Fix curly quotes / dashes
        - Collapse letter-spaced runs ("A B S T R A C T" → "ABSTRACT")
        - Collapse redundant whitespace
        """
        if not text:
            return ""

        # 1) Ligatures and accents
        text = unicodedata.normalize("NFKD", text)
        text = "".join(c for c in text if not unicodedata.combining(c))

        # 2) Curly quotes / dashes
        text = text.replace("\u2019", "'").replace("\u2018", "'")
        text = text.replace("\u201c", '"').replace("\u201d", '"')
        text = text.replace("\u2014", "-").replace("\u2013", "-")

        # 3) Collapse letter-spaced runs per line
        lines = text.split("\n")
        lines = [DocumentParser._collapse_letter_spacing(l) for l in lines]
        text = "\n".join(lines)

        # 4) Normalize whitespace
        text = re.sub(r"[ \t]+", " ", text)

        return text

    @staticmethod
    def _collapse_letter_spacing(line: str) -> str:
        """
        If a line is dominated by single-character tokens, join them:
          "A B S T R A C T"                      → "ABSTRACT"
          "D E S C R I P T I O N -T O-S E Q ..." → "DESCRIPTION-TO-SEQ..."
        Only acts when >= 60% of tokens are single alphanumeric characters.
        """
        stripped = line.strip()
        if not stripped:
            return line

        tokens = stripped.split()
        if len(tokens) < 3:
            return line

        singles = sum(1 for t in tokens if len(t) == 1 and t.isalnum())
        if singles / len(tokens) < 0.6:
            return line

        out = []
        buf = []
        for t in tokens:
            if len(t) == 1 and t.isalnum():
                buf.append(t)
            else:
                if buf:
                    out.append("".join(buf))
                    buf = []
                out.append(t)
        if buf:
            out.append("".join(buf))

        return " ".join(out)

    # ------------------------------------------------------------------
    # Heading detection
    # ------------------------------------------------------------------
    @staticmethod
    def _is_known_heading(text: str) -> bool:
        """
        True if text matches a known heading — tolerant of:
        - trailing colon/period
        - letter-spacing glued into one word ("RELATEDWORK")
        """
        upper = text.upper().strip(" .:")
        if upper in DocumentParser.KNOWN_HEADINGS:
            return True

        compact = re.sub(r"\s+", "", upper)
        for h in DocumentParser.KNOWN_HEADINGS:
            if h.replace(" ", "") == compact:
                return True

        return False

    @staticmethod
    def is_heading(text: str, font_size=None, max_font=None):

        text = DocumentParser.normalize_text(text).strip()

        if not text:
            return False

        # Too long → paragraph
        if len(text.split()) > 12:
            return False

        # Page number
        if text.isdigit():
            return False

        # URLs
        low = text.lower()
        if "http://" in low or "https://" in low or "github.com" in low:
            return False

        # Figure / Table captions
        if re.match(r"^(figure|fig\.|table)\s+\d+", text, re.I):
            return False

        # Footnotes
        if re.match(r"^\d+\s+the\s", text, re.I):
            return False

        # Bullet lists
        if re.match(r"^\([ivx]+\)", text, re.I):
            return False

        # Reference entries
        if re.match(r"^[A-Z][a-z]+,\s+[A-Z]", text):
            return False
        if re.match(r"^[A-Z][a-z]+\s+[A-Z][a-z]+,", text):
            return False

        # Known heading (tolerant of letter-spaced forms)
        if DocumentParser._is_known_heading(text):
            return True

        # Numbered headings: "1 Introduction", "3.1 Description-to-Sequence Learning"
        if re.match(r"^\d+(\.\d+)*\s+[A-Z][A-Za-z\- ]+$", text):
            return True

        # Font-size fallback
        if (
            font_size is not None
            and max_font is not None
            and font_size >= max_font * 0.95
            and len(text.split()) <= 8
        ):
            return True

        return False

    # ------------------------------------------------------------------
    # Metadata
    # ------------------------------------------------------------------
    @staticmethod
    def extract_metadata(doc):

        metadata = doc.metadata or {}

        title = (metadata.get("title") or "").strip()
        # PDFMaker / Word often prefixes with "Title: "
        if title.lower().startswith("title:"):
            title = title[6:].strip()

        return {
            "title": title,
            "author": (metadata.get("author") or "").strip(),
            "subject": metadata.get("subject") or "",
            "keywords": metadata.get("keywords") or "",
            "creator": metadata.get("creator") or "",
            "producer": metadata.get("producer") or "",
            "page_count": len(doc),
        }

    # ------------------------------------------------------------------
    # Block text cleanup
    # ------------------------------------------------------------------
    @staticmethod
    def clean_block_text(text: str) -> str:
        # Join words split by hyphen at line breaks:
        # "halluci-\nnation" → "hallucination"
        text = re.sub(r"-\n", "", text)
        text = text.replace("\n", " ")
        text = re.sub(r"\s+", " ", text)
        return text.strip()

    @staticmethod
    def merge_blocks(blocks):

        if not blocks:
            return []

        merged = []
        current = blocks[0]

        for block in blocks[1:]:

            if current["type"] == "heading" or block["type"] == "heading":
                merged.append(current)
                current = block
                continue

            x0, y0, x1, y1 = current["bbox"]
            bx0, by0, bx1, by1 = block["bbox"]
            vertical_gap = by0 - y1

            if abs(x0 - bx0) < 15 and vertical_gap < 15:
                current["text"] += " " + block["text"]
                current["bbox"] = (
                    min(x0, bx0),
                    min(y0, by0),
                    max(x1, bx1),
                    max(y1, by1),
                )
            else:
                merged.append(current)
                current = block

        merged.append(current)
        return merged

    # ------------------------------------------------------------------
    # Main entry
    # ------------------------------------------------------------------
    @staticmethod
    def parse(pdf_path):

        doc = fitz.open(pdf_path)

        result = {
            "metadata": DocumentParser.extract_metadata(doc),
            "pages": [],
        }

        stop_parsing = False

        for page_number, page in enumerate(doc, start=1):

            if stop_parsing:
                break

            page_dict = {"page": page_number, "blocks": []}
            page_data = page.get_text("dict")

            page_width = page.rect.width
            mid_x = page_width / 2
            max_font = 0

            # Find largest font on page
            for block in page_data["blocks"]:
                if block["type"] != 0:
                    continue
                for line in block["lines"]:
                    for span in line["spans"]:
                        max_font = max(max_font, span["size"])

            full_width_blocks = []
            left_blocks = []
            right_blocks = []

            for block in page_data["blocks"]:

                if block["type"] != 0:
                    continue

                x0, y0, x1, y1 = block["bbox"]
                width = x1 - x0

                if width > page_width * 0.70:
                    full_width_blocks.append(block)
                elif x1 <= mid_x:
                    left_blocks.append(block)
                elif x0 >= mid_x:
                    right_blocks.append(block)
                else:
                    full_width_blocks.append(block)

            double_column = len(left_blocks) >= 3 and len(right_blocks) >= 3

            if double_column:
                ordered_blocks = []
                ordered_blocks.extend(
                    sorted(full_width_blocks, key=lambda b: b["bbox"][1])
                )
                ordered_blocks.extend(
                    sorted(left_blocks, key=lambda b: b["bbox"][1])
                )
                ordered_blocks.extend(
                    sorted(right_blocks, key=lambda b: b["bbox"][1])
                )
            else:
                ordered_blocks = sorted(
                    [b for b in page_data["blocks"] if b["type"] == 0],
                    key=lambda b: b["bbox"][1],
                )

            parsed_blocks = []

            for block in ordered_blocks:

                spans = []
                largest_font = 0

                for line in block["lines"]:
                    for span in line["spans"]:
                        txt = span["text"].strip()
                        if not txt:
                            continue
                        spans.append(txt)
                        largest_font = max(largest_font, span["size"])

                if not spans:
                    continue

                text = " ".join(s for s in spans if s.strip())
                text = DocumentParser.clean_block_text(text)
                # KEY: normalize ligatures + letter-spacing here
                text = DocumentParser.normalize_text(text)

                if not text:
                    continue

                lower = text.lower()

                if lower.startswith(
                    ("references", "bibliography", "acknowledgement", "acknowledgments")
                ):
                    stop_parsing = True
                    break

                block_type = (
                    "heading"
                    if DocumentParser.is_heading(text, largest_font, max_font)
                    else "paragraph"
                )

                parsed_blocks.append(
                    {"type": block_type, "text": text, "bbox": block["bbox"]}
                )

            parsed_blocks = DocumentParser.merge_blocks(parsed_blocks)

            for block in parsed_blocks:
                page_dict["blocks"].append(
                    {"type": block["type"], "text": block["text"]}
                )

            result["pages"].append(page_dict)

        doc.close()
        return result