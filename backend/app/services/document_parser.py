import pymupdf as fitz
import re


class DocumentParser:

    HEADING_PATTERNS = [
        r"^\d+\.?\s+[A-Z].*",
        r"^[IVXLC]+\.\s+.*",
        r"^(ABSTRACT|INTRODUCTION|RELATED WORK|LITERATURE REVIEW|BACKGROUND|METHODOLOGY|METHODS|PROPOSED METHOD|EXPERIMENTS|RESULTS|DISCUSSION|CONCLUSION|FUTURE WORK|REFERENCES)$"
    ]

    @staticmethod
    def is_heading(text: str, font_size=None, max_font=None):

        text = text.strip()

        if not text:
            return False

        # Too long → paragraph
        if len(text.split()) > 12:
            return False

        # Page number
        if text.isdigit():
            return False

        # URLs
        if "http://" in text.lower() or \
        "https://" in text.lower() or \
        "github.com" in text.lower():
            return False

        # Figure/Table captions
        if re.match(r"^(figure|fig\.|table)\s+\d+", text, re.I):
            return False

        # Footnotes
        if re.match(r"^\d+\s+the\s", text, re.I):
            return False

        # Bullet lists
        if re.match(r"^\([ivx]+\)", text, re.I):
            return False

        # References
        if re.match(r"^[A-Z][a-z]+,\s+[A-Z]", text):
            return False

        if re.match(r"^[A-Z][a-z]+\s+[A-Z][a-z]+,", text):
            return False

        known = {
            "ABSTRACT",
            "INTRODUCTION",
            "RELATED WORK",
            "BACKGROUND",
            "METHOD",
            "METHODS",
            "METHODOLOGY",
            "EXPERIMENTS",
            "EXPERIMENTAL SETUP",
            "RESULTS",
            "DISCUSSION",
            "CONCLUSION",
            "LIMITATIONS",
            "ETHICAL CONSIDERATIONS",
            "REFERENCES",
            "ACKNOWLEDGEMENT",
            "ACKNOWLEDGMENTS",
            "APPENDIX",
        }

        if text.upper() in known:
            return True

        # 1 Introduction
        # 2 Related Work
        # 3.1 Hallucination Taxonomy

        if re.match(
            r"^\d+(\.\d+)*\s+[A-Z][A-Za-z\- ]+$",
            text
        ):
            return True

        if (
            font_size is not None
            and max_font is not None
            and font_size >= max_font * 0.95
            and len(text.split()) <= 8
        ):
            return True

        return False

    @staticmethod
    def extract_metadata(doc):

        metadata = doc.metadata

        return {
            "title": metadata.get("title"),
            "author": metadata.get("author"),
            "subject": metadata.get("subject"),
            "keywords": metadata.get("keywords"),
            "creator": metadata.get("creator"),
            "producer": metadata.get("producer"),
            "page_count": len(doc)
        }
    import re

    @staticmethod
    def clean_block_text(text: str) -> str:
        # Join words split by hyphen at line breaks:
        # "halluci-\nnation" -> "hallucination"
        text = re.sub(r"-\n", "", text)

        # Replace remaining newlines with spaces
        text = text.replace("\n", " ")

        # Collapse repeated whitespace
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    @staticmethod
    def merge_blocks(blocks):

        if not blocks:
            return []

        merged = []

        current = blocks[0]

        for block in blocks[1:]:

            # Never merge headings
            if current["type"] == "heading" or block["type"] == "heading":

                merged.append(current)

                current = block

                continue

            x0, y0, x1, y1 = current["bbox"]

            bx0, by0, bx1, by1 = block["bbox"]

            vertical_gap = by0 - y1

            # Merge paragraphs that are close together
            if (
                abs(x0 - bx0) < 15 and
                vertical_gap < 15
            ):

                current["text"] += " " + block["text"]

                current["bbox"] = (
                    min(x0, bx0),
                    min(y0, by0),
                    max(x1, bx1),
                    max(y1, by1)
                )

            else:

                merged.append(current)

                current = block

        merged.append(current)

        return merged

    @staticmethod
    def parse(pdf_path):

        doc = fitz.open(pdf_path)

        result = {
            "metadata": DocumentParser.extract_metadata(doc),
            "pages": []
        }

        stop_parsing = False

        for page_number, page in enumerate(doc, start=1):

            if stop_parsing:
                break

            page_dict = {
                "page": page_number,
                "blocks": []
            }

            page_data = page.get_text("dict")

            page_width = page.rect.width
            mid_x = page_width / 2

            max_font = 0

            # -----------------------------
            # Find largest font on page
            # -----------------------------
            for block in page_data["blocks"]:

                if block["type"] != 0:
                    continue

                for line in block["lines"]:
                    for span in line["spans"]:
                        max_font = max(max_font, span["size"])

            full_width_blocks = []
            left_blocks = []
            right_blocks = []

            # -----------------------------
            # Split blocks
            # -----------------------------
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

            # -----------------------------
            # Detect layout
            # -----------------------------
            double_column = (
                len(left_blocks) >= 3 and
                len(right_blocks) >= 3
            )

            if double_column:

                ordered_blocks = []

                ordered_blocks.extend(
                    sorted(full_width_blocks,
                        key=lambda b: b["bbox"][1])
                )

                ordered_blocks.extend(
                    sorted(left_blocks,
                        key=lambda b: b["bbox"][1])
                )

                ordered_blocks.extend(
                    sorted(right_blocks,
                        key=lambda b: b["bbox"][1])
                )

            else:

                ordered_blocks = sorted(
                    [b for b in page_data["blocks"] if b["type"] == 0],
                    key=lambda b: b["bbox"][1]
                )

            parsed_blocks = []

            # -----------------------------
            # Convert blocks
            # -----------------------------
            for block in ordered_blocks:

                spans = []

                largest_font = 0

                for line in block["lines"]:

                    for span in line["spans"]:

                        txt = span["text"].strip()

                        if not txt:
                            continue

                        spans.append(txt)

                        largest_font = max(
                            largest_font,
                            span["size"]
                        )

                if not spans:
                    continue

                text = " ".join(
                    s for s in spans if s.strip()
                )

                text = DocumentParser.clean_block_text(text)

                if not text:
                    continue

                lower = text.lower()

                # -----------------------------
                # Stop after references
                # -----------------------------
                if lower.startswith((
                    "references",
                    "bibliography",
                    "acknowledgement",
                    "acknowledgments"
                )):
                    stop_parsing = True
                    break

                block_type = (
                    "heading"
                    if DocumentParser.is_heading(
                        text,
                        largest_font,
                        max_font
                    )
                    else "paragraph"
                )

                parsed_blocks.append({

                    "type": block_type,

                    "text": text,

                    "bbox": block["bbox"]

                })

            # -----------------------------
            # Merge neighbouring paragraphs
            # -----------------------------
            parsed_blocks = DocumentParser.merge_blocks(
                parsed_blocks
            )

            # -----------------------------
            # Remove bbox
            # -----------------------------
            for block in parsed_blocks:

                page_dict["blocks"].append({

                    "type": block["type"],

                    "text": block["text"]

                })

            result["pages"].append(page_dict)

        doc.close()

        return result