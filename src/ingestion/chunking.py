from langchain_text_splitters import RecursiveCharacterTextSplitter

def split_documents(documents):
    splitter=RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50
    )
    chunks=splitter.split_documents(documents)
    for chunk in chunks:
        print(chunk.metadata)
        print(chunk.page_content)
    return chunks


