from langchain_community.document_loaders import DirectoryLoader,TextLoader

def load_documents(path="data"):
    documents = []
    loaders=[DirectoryLoader(
        path=path,
        glob="**/*.md",
        loader_cls=TextLoader
        ),
        DirectoryLoader(
            path=path,
            glob="**/*.txt",
            loader_cls=TextLoader
        )]
    for loader in loaders:
        documents.extend(loader.load())
    if len(documents)==0:
        raise FileNotFoundError("Zero files found.")
    for doc in documents:
        print(doc.metadata)
        print(doc.page_content)
    return documents

