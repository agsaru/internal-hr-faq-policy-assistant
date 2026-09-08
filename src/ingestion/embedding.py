from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

embedder = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

def generate_embeddings(chunks):
    vector_store = Chroma(
        persist_directory="./chroma_db",
        collection_name="hr_faq_policies",
        embedding_function=embedder
    )
    
    vector_store.add_documents(chunks)
    return vector_store
