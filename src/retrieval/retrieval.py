from src.ingestion.embedding import get_vector_store


def search_documents(query, k=5):

    vector_store = get_vector_store()

    results = vector_store.similarity_search_with_score(query,k=k)

    for index, (document, score) in enumerate(results):

        print(f"RESULT {index + 1}")
        print(f"Score: {score}")
        print(f"Document: {document.metadata.get('document')}")
        print(f"Section: {document.metadata.get('section')}")
        print(f"Chunk: {document.metadata.get('chunk_index')}")
        print("Content:")
        print(document.page_content)

    return results