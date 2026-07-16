from fastapi import APIRouter, UploadFile, File, HTTPException
import os
import uuid

from app.services.pdf_service import PDFService
from app.services.paper_service import PaperService

router = APIRouter()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

from app.core.container import container


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):

    # Validate file type
    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are allowed."
        )

    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}.pdf"

    file_path = os.path.join(
        UPLOAD_DIR,
        unique_filename
    )

    # Save uploaded file
    contents = await file.read()

    with open(file_path, "wb") as f:
        f.write(contents)

    # Extract PDF metadata
    metadata = PDFService.extract_metadata(file_path)

    # Process the paper
    result = container.paper_service.process_pdf(
        file_path=file_path,
        metadata=metadata
    )

    # Return response
    return {
        "message": "PDF uploaded and processed successfully",
        "original_filename": file.filename,
        "saved_filename": unique_filename,
        "file_size": len(contents),
        **result
    }