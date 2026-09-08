import os

from fastapi import APIRouter, UploadFile, File, HTTPException

from src.ingestion.loader import load_documents
from src.ingestion.chunking import split_documents
from src.ingestion.embedding import generate_embeddings,delete_document_embeddings


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
        raise HTTPException(status_code=400,detail="Filename is missing.")

    extension = os.path.splitext(file.filename)[1].lower()

    if extension not in {".md", ".txt"}:
        raise HTTPException(status_code=400,detail="Only .md and .txt files are supported.")

    data = await file.read()

    if not data:
        raise HTTPException(status_code=400,detail="Uploaded file is empty.")

    os.makedirs("data", exist_ok=True)

    file_path = os.path.join("data",file.filename)

    with open(file_path, "wb") as f:
        f.write(data)

    try:
        documents = load_documents(file_path)

        for document in documents:
            document.metadata["document"] = file.filename

        chunks = split_documents(documents)

        generate_embeddings(chunks)

    except Exception as exc:
        if os.path.exists(file_path):
            os.remove(file_path)

        raise HTTPException(status_code=500,detail=f"Failed to process document:{str(exc)}")

    return {"message":"File uploaded successfully","filename": file.filename}

@router.delete("/{filename}")
def delete_document(filename: str):

    file_path = os.path.join("data", filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404,detail="Document not found.")

    delete_document_embeddings(filename)
    os.remove(file_path)

    return { "message": "Document deleted successfully."}