from langchain_core.documents import Document
from langchain_community.retrievers import BM25Retriever
from src.ingestion.embedding import get_vector_store

def search_documents(query, k=5):
    vector_store = get_vector_store()

    vector_results = vector_store.similarity_search_with_score(query, k=k)
    data = vector_store._collection.get(include=["documents", "metadatas"])

    if not data or not data["documents"]:
        return []

    documents = []
    for content, metadata in zip(data["documents"], data["metadatas"]):
        documents.append(Document(page_content=content, metadata=metadata))

    bm25_retriever = BM25Retriever.from_documents(documents)
    bm25_retriever.k = k
    bm25_results = bm25_retriever.invoke(query)

    scores = {}
    document_map = {}

    for rank, (document, score) in enumerate(vector_results):
        key = (document.metadata.get("document", "Unknown"), document.metadata.get("chunk_index", -1))
        scores[key] = scores.get(key, 0) + 1/(60+rank+1)
        document_map[key] = document

    for rank, document in enumerate(bm25_results):
        key = (document.metadata.get("document", "Unknown"), document.metadata.get("chunk_index", -1))
        scores[key] = scores.get(key, 0) + 1/(60+rank+1)
        document_map[key] = document

    ranked_results = sorted(scores.items(), key=lambda item: item[1], reverse=True)

    results = []
    for key, score in ranked_results[:k]:
        results.append((document_map[key], score))

    for index, (document, score) in enumerate(results):
        print(f"RESULT {index + 1}")
        print(f"Score: {score}")
        print(f"Document: {document.metadata.get('document')}")
        print(f"Section: {document.metadata.get('section')}")
        print(f"Chunk: {document.metadata.get('chunk_index')}")
        print("Content:")
        print(document.page_content)

    return results