from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

def generate_embeddings(chunks):
    embedder=HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')
    vector_store=Chroma.from_documents(
        documents=chunks,
        embedding=embedder,
        persist_directory="./chroma_db",
        collection_name="hr_faq_policies"
    )
    return vector_store
