# HR Policy Assistant

This project is a small RAG-based HR Policy Assistant.

The HR uploads policy documents, and employees can ask questions about those policies. The system searches the uploaded documents and gives an answer with the document and section it came from. If the answer is not in the uploaded policies, it refuses instead of guessing.

The project supports `.md`, `.txt`, and `.pdf` files.

## Tech Stack

| Component | Technology |
| :--- | :--- |
| **API Backend** | FastAPI + Uvicorn |
| **Frontend UI** | Streamlit |
| **Document Parsing** | Unstructured (`unstructured[md,pdf]`) |
| **Chunking** | Title-aware (`chunk_by_title`) |
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` |
| **Vector Store** | ChromaDB (`langchain-chroma`) |
| **Keyword Search** | BM25 (`rank-bm25`) |
| **Hybrid Retrieval** | LangChain `EnsembleRetriever` |
| **LLM Generation** | Google Gemini (`langchain-google-genai`) |
| **Data Validation** | Pydantic |


## Project structure

```text
├── src
│   ├── api
│   │   ├── routes
│   │   │   ├── chat.py
│   │   │   └── documents.py
│   │   └── main.py
│   ├── generation
│   │   └── generator.py
│   ├── ingestion
│   │   ├── chunking.py
│   │   ├── embedding.py
│   │   └── loader.py
│   ├── models
│   │   └── schema.py
│   ├── retrieval
│   │   └── retrieval.py
│   └── ui
│       └── app.py
├── DESIGN.md
├── README.md
├── requirements.txt
└── .env.example
```

## Setup

Python packages are listed in `requirements.txt`.

Install them with:

```bash
pip install -r requirements.txt
```

The application uses Gemini for the final answer, so a Gemini API key is needed.

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
BACKEND_API_URL=http://127.0.0.1:8000
```

Do not commit the `.env` file or the API key.

## Running the project

### 1. Start the backend

From the project root:

```bash
uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```

The FastAPI backend will run at:

```text
http://127.0.0.1:8000
```

### 2. Start the UI

Open another terminal and run:

```bash
streamlit run src/ui/app.py
```

## How to use it

### HR / Admin

Select `HR` from the sidebar.

Upload a `.md`, `.txt`, or `.pdf` policy.

The backend then:

1. saves the file in `data/`
2. loads the document
3. creates chunks
4. adds document and section metadata
5. removes old embeddings for the same filename
6. creates embeddings
7. stores everything in ChromaDB


### Employee

Select `Employee`.

Type a question and press **Ask**.

For example:

```text
What is the casual leave carry-forward limit?
```

A successful response looks like:

```json
{
  "answer": "....",
  "citations": [
    {
      "document": "leave-policy.md",
      "section": "Casual Leave"
    }
  ]
}
```

For a question that is not answered by the uploaded policies, the system returns:

```text
This information is not provided in our HR policy documents.
Please contact the HR team at hr@example.com.
```

The citation list is empty in that case.

## API Endpoints

When the backend is running, interactive API docs are accessible at:
- **Swagger UI:** `http://127.0.0.1:8000/docs`
- **ReDoc:** `http://127.0.0.1:8000/redoc`

Core endpoints:
- `POST /documents/upload` — Upload and index a `.md`, `.txt`, or `.pdf` policy.
- `GET /documents/` — List uploaded policy documents.
- `DELETE /documents/{filename}` — Delete a policy and its stored embeddings.
- `POST /chat/ask` — Ask a question and receive a structured answer with citations.

## Design

For full details on how the system is designed and the trade-offs made, see **[DESIGN.md](DESIGN.md)**.
