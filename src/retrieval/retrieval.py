from langchain_classic.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

from src.ingestion.embedding import get_vector_store

def search_documents(query, k=5):
    vector_store = get_vector_store()

    vector_retriever = vector_store.as_retriever(search_kwargs={"k": k})
    data = vector_store._collection.get(include=["documents", "metadatas"])

    if not data or not data["documents"]:
        return []

    documents = []
    for content, metadata in zip(data["documents"], data["metadatas"]):
        documents.append(Document(page_content=content, metadata=metadata))

    bm25_retriever = BM25Retriever.from_documents(documents)
    bm25_retriever.k = k
    ensemble_retriever = EnsembleRetriever(
        retrievers=[vector_retriever, bm25_retriever],
        weights=[0.5, 0.5]
    )

    results = ensemble_retriever.invoke(query)[:k]

    for document in results:
        print(f"Document: {document.metadata.get('document')}")
        print(f"Section: {document.metadata.get('section')}")
        print("Content:")
        print(document.page_content[:100])

    return results