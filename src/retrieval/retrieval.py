from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma

embedder=HuggingFaceEmbeddings(model_name='sentence-transformers/all-MiniLM-L6-v2')

def search_documents(query,k=3):
   
    vector_store=Chroma(
        persist_directory="./chroma_db",
        embedding_function=embedder,
        collection_name="hr_faq_policies"
    )
    documents=vector_store.similarity_search(query,k=k)
    return documents

