from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings


embedder = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)

def get_vector_store():

    return Chroma(
        persist_directory="./chroma_db",
        collection_name="hr_faq_policies",
        embedding_function=embedder
    )

def generate_embeddings(chunks):

    vector_store = get_vector_store()

    vector_store.add_documents(chunks)

    results = vector_store._collection.get(
        limit=1,
        include=["documents", "metadatas"]
    )

    if results["ids"]:

        print("\nStored chunk:")
        print(f"ID: {results['ids'][0]}")
        print(f"Document: {results['documents'][0]}")
        print(f"Metadata: {results['metadatas'][0]}")

    return vector_store


def delete_document_embeddings(filename):

    vector_store = get_vector_store()
    results = vector_store._collection.get(where={"document":filename})

    if results["ids"]:
        vector_store._collection.delete(ids=results["ids"])