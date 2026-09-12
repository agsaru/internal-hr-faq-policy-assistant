import os

from fastapi import APIRouter, File, HTTPException, UploadFile

from src.ingestion.chunking import split_documents
from src.ingestion.embedding import delete_document_embeddings, generate_embeddings
from src.ingestion.loader import load_documents

router = APIRouter()


@router.get("/")
def list_documents():
    if not os.path.exists("data"):
        return []

    documents = []
    for filename in os.listdir("data"):
        path = os.path.join("data", filename)
        if os.path.isfile(path):
            documents.append({"filename": filename})

    return documents


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is missing.")

    filename = os.path.basename(file.filename)
    extension = os.path.splitext(filename)[1].lower()
    if extension not in {".md", ".txt", ".pdf"}:
        raise HTTPException(
            status_code=400,
            detail="Only .md, .txt and .pdf files are supported.",
        )

    data = await file.read()
    if not data:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    os.makedirs("data", exist_ok=True)
    file_path = os.path.join("data", filename)

    with open(file_path, "wb") as f:
        f.write(data)

    try:
        elements = load_documents(file_path)

        for element in elements:
            element.metadata.filename = filename

        chunks = split_documents(elements)
        delete_document_embeddings(filename)
        generate_embeddings(chunks)
    except Exception as exc:
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process document: {exc}",
        ) from exc

    return {"message": "File uploaded successfully", "filename": filename}


@router.delete("/{filename}")
def delete_document(filename: str):
    filename = os.path.basename(filename)
    file_path = os.path.join("data", filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Document not found.")

    delete_document_embeddings(filename)
    os.remove(file_path)

    return {"message": "Document deleted successfully."}