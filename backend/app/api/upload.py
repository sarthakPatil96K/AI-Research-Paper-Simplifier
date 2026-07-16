from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import uuid

from app.services.pdf_service import PDFService

router = APIRouter()

UPLOAD_DIR = "uploads"

os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    unique_filename = f"{uuid.uuid4()}.pdf"

    file_path = os.path.join(
        UPLOAD_DIR,
        unique_filename
    )

    contents = await file.read()

    with open(file_path, "wb") as f:
        f.write(contents)

    metadata = PDFService.extract_metadata(file_path)

    text_data = PDFService.extract_text_from_pdf(file_path)
    from app.services.chunk_service import ChunkService
    clean_text = ChunkService.clean_text(
    text_data["full_text"]
    )

    sections = ChunkService.extract_sections(
        clean_text
    )

    chunks = ChunkService.create_chunks(
        sections
    )

     

    return {

    "message": "PDF Uploaded Successfully",

    "paper": metadata,

    "sections": list(sections.keys()),

    "total_characters": len(clean_text),

    "total_chunks": len(chunks),

    "chunk_preview": chunks[:2]

    }