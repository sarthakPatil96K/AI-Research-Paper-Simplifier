import fitz
import re


class PDFService:

    @staticmethod
    def extract_text_from_pdf(file_path):

        document = fitz.open(file_path)

        full_text = ""

        pages = []

        for page_number, page in enumerate(document):

            text = page.get_text()

            pages.append({
                "page": page_number + 1,
                "text": text
            })

            full_text += text + "\n"

        document.close()

        return {
            "full_text": full_text,
            "pages": pages
        }


    @staticmethod
    def extract_metadata(file_path):

        document = fitz.open(file_path)

        metadata = document.metadata

        page_count = document.page_count

        document.close()

        return {

            "title": metadata.get("title") or "Unknown",

            "author": metadata.get("author") or "Unknown",

            "subject": metadata.get("subject") or "Unknown",

            "keywords": metadata.get("keywords") or "Unknown",

            "creator": metadata.get("creator") or "Unknown",

            "producer": metadata.get("producer") or "Unknown",

            "pages": page_count

        }


    @staticmethod
    def detect_sections(full_text):

        headings = [

            "Abstract",

            "Introduction",

            "Related Work",

            "Literature Review",

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

        detected = []

        for heading in headings:

            match = re.search(
                rf"\b{re.escape(heading)}\b",
                full_text,
                re.IGNORECASE
            )

            if match:

                detected.append({
                    "section": heading,
                    "position": match.start()
                })

        detected.sort(key=lambda x: x["position"])

        return detected