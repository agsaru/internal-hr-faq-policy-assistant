from langchain_community.document_loaders import TextLoader


def load_documents(path):
    loader = TextLoader(
        path,
        encoding="utf-8"
    )

    documents = loader.load()

    if not documents:
        raise FileNotFoundError("File could not be loaded.")

    return documents
