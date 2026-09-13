# Technical Design

## 1. Architecture

The system is divided into two main flows: **document ingestion** and **question answering**. Documents are processed once and stored as searchable vectors, while employee questions are validated, retrieved against the indexed policies, and passed to the LLM only with relevant policy context.

```text
                                      HR POLICY ASSISTANT
                         ─────────────────────────────────────────

      ADMIN / HR                                                     EMPLOYEE
          │                                                              │
          │ Upload policy                                                │ Ask question
          │ (.md / .txt / .pdf)                                          │
          ▼                                                              ▼
┌──────────────────────────────┐                            ┌──────────────────────────────┐
│        FastAPI API           │                            │        FastAPI API           │
│                              │                            │                              │
│  /documents/upload           │                            │  /chat/ask                  │
│  /documents/                 │                            │                              │
│  /documents/{filename}       │                            │  Validate non-empty query   │
└──────────────┬───────────────┘                            └──────────────┬───────────────┘
               │                                                           │
               ▼                                                           ▼
┌──────────────────────────────┐                            ┌──────────────────────────────┐
│      Document Loading        │                            │      Relevance Check         │
│                              │                            │                              │
│ Unstructured partition()     │                            │ Dense similarity search      │
│                              │                            │ Threshold = 0.15             │
│ .md / .txt / .pdf            │                            └──────────────┬───────────────┘
│                              │                                           │
└──────────────┬───────────────┘                              ┌────────────┴────────────┐
               │                                              │                         │
               ▼                                           score < 0.15             score >= 0.15
┌──────────────────────────────┐                              │                         │
│       Document Chunking      │                              ▼                         ▼
│                              │                   ┌──────────────────────┐  ┌──────────────────────────┐
│ chunk_by_title()             │                   │     SAFE REFUSAL     │  │     Hybrid Retrieval     │
│                              │                   │                      │  │                          │
│                              │                   │ "Information is not  │  │ Dense vector search      │
│                              │                   │ provided..."         │  │ +                        │
│                              │                   │                      │  │ BM25 keyword search      │
│                              │                   │ Contact HR           │  │                          │
└──────────────┬───────────────┘                   └──────────────────────┘  │ weights = [0.5, 0.5]     │
               │                                                             │                          │
               │                                                             └────────────┬─────────────┘
               ▼                                                                          │
┌──────────────────────────────┐                                                          ▼
│      Chunk Metadata          │                                             ┌──────────────────────────┐
│                              │                                             │     Retrieved Chunks     │
│ document                     │                                             │                          │
│ section                      │                                             │ Top relevant policy      │
│ chunk_index                  │                                             │ chunks                   │
│ filename / parser metadata   │                                             └────────────┬─────────────┘
└──────────────┬───────────────┘                                                          │
               │                                                                         ▼
               ▼                                                          ┌──────────────────────────┐
┌──────────────────────────────┐                                          │    Gemini Generation     │
│      Local Embeddings        │                                          │                          │
│                              │                                          │ Context = retrieved      │
│ HuggingFaceEmbeddings        │                                          │ policy chunks only       │
│                              │                                          │                          │
│ all-MiniLM-L6-v2             │                                          │ No guessing / inventing  │
│                              │                                          └────────────┬─────────────┘
└──────────────┬───────────────┘                                                       │
               │                                                                        ▼
               ▼                                                          ┌──────────────────────────┐
        ╔══════════════════════╗                                          │   Structured LLM Output  │
        ║       Chroma         ║                                          │ answer                   │
        ║    Vector Store      ║                                          │ documents_used[]         │
        ║                      ║                                          │ sections_used[]          │
        ║ hr_faq_policies      ║                                          └────────────┬─────────────┘
        ║                      ║                                                       │
        ║ chunk vectors        ║                                                       ▼
        ║ + metadata           ║                                          ┌──────────────────────────┐
        ╚══════════════════════╝                                          │   Citation Validation    │
                                                                          │                          │
                                                                          │  Verify documents_used   │
                                                                          │  & sections_used against │
                                                                          │  retrieved chunk metadata│
                                                                          └────────────┬─────────────┘
                                                                                      │
                                                                                      ▼
                                                                         ┌──────────────────────────┐
                                                                         │     Final JSON Response  │
                                                                         │                          │
                                                                         │ {                        │
                                                                         │   answer: "...",         │
                                                                         │   citations: [           │
                                                                         │     {                    │
                                                                         │       document: "...",   │
                                                                         │       section: "..."     │
                                                                         │     }                    │
                                                                         │   ]                      │
                                                                         │ }                        │
                                                                         └──────────────────────────┘
```

### Components

| Component | Responsibility |
| :--- | :--- |
| `src/api/main.py` | Initializes FastAPI, mounts document and chat routers, and configures server startup. |
| `src/api/routes/documents.py` | Handles `/upload`, `/`, and `/{filename}` endpoints for uploading, listing, and deleting policies. |
| `src/api/routes/chat.py` | Handles `/ask` endpoint, validates non-empty employee questions, and calls the generator. |
| `src/ingestion/loader.py` | Loads `.md`, `.txt`, and `.pdf` files into structured elements using Unstructured. |
| `src/ingestion/chunking.py` | Splits documents using `chunk_by_title` and attaches document and section metadata. |
| `src/ingestion/embedding.py` | Generates local `all-MiniLM-L6-v2` embeddings and manages ChromaDB vector storage. |
| `src/retrieval/retrieval.py` | Implements the 0.15 relevance check and builds the hybrid EnsembleRetriever (Vector + BM25). |
| `src/generation/generator.py` | Formats context, calls Gemini with strict prompt, and validates citations against retrieved metadata. |
| `src/models/schema.py` | Defines Pydantic models for API requests, responses, and structured LLM output. |
| `src/ui/app.py` | Streamlit frontend with HR upload/management and Employee question-answering views. |


---

## 2. Ingestion & Chunking Strategy

The ingestion pipeline works with any policy document. Any HR policy uploaded as Markdown (`.md`), plain text (`.txt`), or PDF (`.pdf`) is loaded, parsed into structured semantic elements, split into title-aware chunks, and indexed into the vector store.

### 2.1 Document Parsing
Policies are rarely raw text; they contain hierarchical headers, clause numbers, bulleted requirements, and tables. The ingestion system uses `unstructured.partition.auto.partition` to parse incoming files into semantic element objects (`Title`, `NarrativeText`, `UncategorizedText`, `ListItem`, `Table`).

#### Element Structure & Extracted Attributes
Every element parsed by Unstructured contains the element type, raw text, and a rich metadata dictionary:

```python
{
    "type": "UncategorizedText",  # or "Title", "NarrativeText", "ListItem", "Table"
    "text": "Document title: Leave Policy Version: 1.0 Applies to: Full-time employees in India Owner: Human Resources",
    "metadata": {
        "filename": "leave-policy.md",
        "filetype": "text/markdown",
        "file_directory": "data",
        "languages": ["eng"],
        "parent_id": "84d72023023ebba7359d9c240fb2f6fa",
        "category_depth": 0,
        "emphasized_text_contents": ["Document title:", "Version:", "Applies to:", "Owner:"],
        "emphasized_text_tags": ["b", "b", "b", "b"],
        "last_modified": "2026-09-12T13:29:49"
    }
}
```

If an upload fails at any stage of parsing or embedding, the uploaded file is purged from the `data/` directory to prevent orphaned files from desyncing with the vector database.

### 2.2 Chunking: `chunk_by_title`
To keep policy sections and clauses together, the pipeline chunks parsed elements using `unstructured.chunking.title.chunk_by_title`.

Configuration:
- `max_characters = 1000`: Caps chunk size to keep embeddings focused on a single topic.
- `new_after_n_chars = 750`: Breaks at natural section boundaries around 750 characters.
- `overlap = 100`: Preserves continuity across neighboring chunks.
- `combine_text_under_n_chars = 200`: Merges orphan headings or tiny fragments into neighboring sections to avoid noisy, low-signal chunks.

### 2.3 Metadata Enrichment & Section Resolution
When `chunk_by_title` creates a chunk, the original elements that formed it are stored in its metadata.

In `src/ingestion/chunking.py`, `split_documents()` iterates through these original elements to identify the nearest parent heading (`Title`, `Header`, or `ListItem`). It enriches every chunk with:
- `document`: The source filename (e.g. `leave-policy.md`).
- `section`: The nearest parent section title extracted from the document headings (falls back to `"General"` if unsectioned).
- `chunk_index`: The sequential integer index of the chunk within the document.
- Ingestion metadata: Preserves parser attributes like `filetype`, `languages`, and emphasized text.

#### What a Stored Chunk Looks Like
Here is the concrete `Document` object structure created and passed to the vector store:

```python
Document(
    page_content="""2. Leave types

2.1 Casual leave (CL)

Employees receive 12 casual leave days per calendar year. Casual leave is meant for short personal needs and unplanned absences.

Casual leave may be taken in units of half a day or a full day.""",
    metadata={
        "document": "leave-policy.md",
        "filename": "leave-policy.md",
        "section": "2. Leave types",
        "chunk_index": 1,
        "filetype": "text/markdown",
        "languages": ["eng"],
        "emphasized_text_contents": ["12 casual leave days"],
        "emphasized_text_tags": ["b"],
        "last_modified": "2026-09-12T13:29:49"
    }
)
```

### 2.4 Vector Storage & Embeddings
- **Vector DB:** ChromaDB persisted locally at `./chroma_db` under the collection `hr_faq_policies`.
- **Embedding Model:** Local `sentence-transformers/all-MiniLM-L6-v2` running on CPU.
- **Representation:** Generates 384-dimensional dense vectors stored alongside chunk content and metadata.
- **Lifecycle Management:** When a document is re-uploaded or deleted, existing chunks are purged by metadata filter (`document == filename`).

---

## 3. Retrieval Design: Hybrid Search

HR questions typically fall into two categories:
1. **Semantic queries:** An employee asks *"Can I roll over unused time off?"*, while the document states *"Unused casual leave may be carried forward into the next calendar year."*
2. **Keyword exact matches:** An employee asks about *"Clause 4.2"*, *"Tier 2 Dental"*, or specific allowance acronyms (e.g., *"LTA"*).

### Why Hybrid Search?
Dense vector retrieval excels at semantic paraphrasing but can miss exact policy clauses or acronyms. BM25 excels at exact keyword matching but fails when employees rephrase concepts.

I combined both using LangChain's `EnsembleRetriever`:
- **Dense Retriever:** Local `all-MiniLM-L6-v2` embeddings in ChromaDB (weight: `0.5`).
- **Sparse Retriever:** Dynamic `BM25Retriever` constructed from all currently indexed policy chunks (weight: `0.5`).
- **Ranking:** Reciprocal Rank Fusion (RRF) merges dense and sparse rankings to produce the top 5 chunks.

### How Retrieval Works in Practice
When an employee submits a query:

```text
Query: "How many casual leave days do employees receive each year?"
```

1. **Gate 1 Relevance Check:**
   `vector_store.similarity_search_with_relevance_scores(query, k=1)` computes the top cosine similarity against the indexed chunks.
   - If `top_score < 0.15`: The query is out-of-scope or unsupported. Retrieval halts immediately and returns a safe refusal.
   - If `top_score >= 0.15`: The query proceeds to hybrid retrieval. (In this example, top score is `0.6298`, which passes).

2. **Ensemble Retrieval & RRF Fusion:**
   Both retrievers query the corpus in parallel:
   - Dense search surfaces semantically related chunks (matching leave definitions and accrual rules).
   - BM25 matches exact keywords like *"casual leave"*, *"days"*, and *"receive"*.
   - RRF ranks the combined results, placing the most relevant section (`2. Leave types`) at Rank 1, followed by related accrual and carry-forward clauses in the top 5.

---

## 4. Grounding & Anti-Hallucination

Prompt engineering alone is insufficient to prevent hallucinations. My design uses a **two-gate verification strategy**: one check *before* the LLM is invoked, and one check *after*.

```text
Employee Question
       │
       ▼
[Gate 1: Relevance Check]
Score < 0.15? ──► YES ──► Immediate Safe Refusal ("This information is not provided...")
       │ (No, score >= 0.15)
       ▼
Hybrid Search (Vector + BM25 Top 5 Chunks)
       │
       ▼
LLM Generation (Gemini 2.5 Flash Lite + Strict Instructions)
       │
       ▼
[Gate 2: Citation Verification]
Extract LLM `documents_used` & `sections_used`
Verify each against retrieved chunk metadata (document & section)
       │
       ▼
Final JSON Response (Answer + Validated Citations)
```

### 4.1 Gate 1: Pre-Generation Relevance Threshold
Before invoking the model, the system evaluates semantic similarity against the vector store:
```python
RELEVANCE_THRESHOLD = 0.15
```
If the best chunk's similarity score is below `0.15`, the query is deemed off-policy or unsupported. The request returns immediately with a safe refusal without calling Gemini:
> *"This information is not provided in our HR policy documents. Please contact the HR team at hr@example.com."*

This protects against answering completely unrelated questions (e.g., coding, DevOps, or non-existent company benefits) while saving external API costs and latency.

### 4.2 Prompt Construction & Strict Constraints
When retrieval passes Gate 1, `generator.py` formats the retrieved chunks into an isolated `SOURCES:` block:

```text
SOURCES:
Document: leave-policy.md
Section: 2. Leave types
Content:
2. Leave types

2.1 Casual leave (CL)

Employees receive 12 casual leave days per calendar year. Casual leave is meant for short personal needs and unplanned absences.

Casual leave may be taken in units of half a day or a full day.

... (additional retrieved chunks)

QUESTION:
How many casual leave days do employees receive each year?
```

The system prompt enforces:
- **Strict document grounding:** Answers must be formulated solely from facts in `SOURCES`.
- **Exact document and section naming:** When citations are provided, `documents_used` must match exact document filenames in `SOURCES`, and `sections_used` must match exact section names from `SOURCES`. Paraphrasing, shortening, or inventing names is strictly prohibited.
- **Document-level citation support:** Citations may cite a document without a section (`documents_used` may contain a document even when `sections_used` is empty).
- **Handling multi-part questions:** Answer supported parts clearly while refusing unsupported parts individually.
- **No internal meta-talk:** Prohibits robotic phrases like *"Based on the retrieved context..."* or *"According to the vector search..."*.

### 4.3 Gate 2: Post-Generation Citation Validation
Gemini generates structured output with three fields:
- **`answer`**: The grounded response formulated strictly from the provided chunks.
- **`documents_used`**: A list of exact document filenames the model consulted (e.g., `["leave-policy.md"]`).
- **`sections_used`**: A list of exact section titles the model consulted (e.g., `["2. Leave types"]`). Optional or empty if citing at the document level or if no sections exist.

```json
{
  "answer": "Employees receive 12 casual leave days per calendar year.",
  "documents_used": ["leave-policy.md"],
  "sections_used": ["2. Leave types"]
}
```

**Verification Logic:**
To prevent the model from hallucinating sources or inventing document and section names:
1. **Document Validation:** The backend iterates through `documents_used` and checks each document name against the `document` metadata of the retrieved chunks (case-insensitively). Any document name not present in the retrieved chunks is discarded.
2. **Document-Level Fallback:** If `sections_used` is empty (or no sections apply), the citation is added as `{ "document": matching_document, "section": None }`.
3. **Section Validation:** When `sections_used` is provided, the backend verifies each section name against the `section` metadata of the matching chunks for that document (case-insensitively). Any section not found in the retrieved context for that document is ignored.
4. **Citation Construction & Deduplication:** Validated document and section pairs are structured as `{ "document": "...", "section": "..." }`, deduplicated, and returned in the final citations list.

This ensures users only receive citations that genuinely exist in the retrieved policy chunks.

### 4.4 Handling Policy Exclusions & Unanswerable Queries
- **Explicit exclusions:** When an employee asks about a benefit that policies explicitly deny (e.g., *"Can I expense gym equipment?"*), the assistant retrieves the relevant exclusion clause, quotes the policy accurately, and cites the corresponding section (e.g. `4. Wellness`).
- **Completely unmentioned topics:** If an inquiry has no relevant policy clauses (e.g., questions about public Wi-Fi or internal server configurations), Gate 1 or Gate 2 returns the standardized refusal message with HR contact details and an empty citations array.

---

## 5. API Contracts & Schemas

The FastAPI backend exposes endpoints for document lifecycle and question answering.

### Endpoints

#### `POST /documents/upload`
Uploads and indexes a policy document (`.md`, `.txt`, or `.pdf`).
- **Request:** `multipart/form-data` with `file`
- **Response:**
  ```json
  {
    "message": "File uploaded successfully",
    "filename": "leave-policy.md"
  }
  ```

#### `GET /documents/`
Lists all currently indexed policy documents.
- **Response:**
  ```json
  [
    {
      "filename": "leave-policy.md"
    }
  ]
  ```

#### `DELETE /documents/{filename}`
Deletes a policy document and purges its stored embeddings.
- **Response:**
  ```json
  {
    "message": "Document deleted successfully."
  }
  ```

#### `POST /chat/ask`
Submits an employee question and returns a grounded answer with citations.
- **Request:**
  ```json
  {
    "question": "How many casual leave days do employees receive each year?"
  }
  ```
- **Response (Supported Answer):**
  ```json
  {
    "answer": "Employees receive 12 casual leave days per calendar year.",
    "citations": [
      {
        "document": "leave-policy.md",
        "section": "2. Leave types"
      }
    ]
  }
  ```
- **Response (Safe Refusal):**
  ```json
  {
    "answer": "This information is not provided in our HR policy documents. Please contact the HR team at hr@example.com.",
    "citations": []
  }
  ```

---

### Schemas

All request and response structures are validated using Pydantic in `src/models/schema.py`:

| Schema | Attributes | Purpose |
| :--- | :--- | :--- |
| `Question` | `question: str` | Validates that incoming employee queries are non-empty strings. |
| `Citation` | `document: str`, `section: Optional[str] = None` | Represents a single verified document and optional section reference. |
| `Answer` | `answer: str`, `citations: List[Citation]` | The final response object returned by the `/chat/ask` endpoint. |
| `LLMResponse` | `answer: str`, `documents_used: List[str] = []`, `sections_used: List[str] = []` | Enforces structured output on Gemini during answer generation. |

### Schema Rationale
- **Predictable API responses:** Returning structured JSON (`citations: List[Citation]`) keeps the frontend simple and avoids parsing citations out of free-form text.
- **Two-step citation verification:** `LLMResponse` captures raw `documents_used` and `sections_used` first, allowing the backend to independently verify document filenames and section headings against actual retrieved chunk metadata before assembling verified `Citation` objects in `Answer`.
- **Support for unsectioned documents:** Having `section: Optional[str] = None` in `Citation` allows the system to cite documents that do not have distinct headings or when the LLM references an entire document without specific sections.

---

## 6. Trade-Offs & Decisions Considered

### 6.1 Title-Aware Chunking over Fixed-Size Splitting
HR policies are naturally divided by headers—like eligibility, carry-forward caps, or health tiers. A standard character or recursive splitter chops text strictly by character length, which often cuts through paragraphs or separates a section heading from the rules under it. Using `chunk_by_title` keeps headings attached to their clauses. This ensures the retrieved chunks contain complete, coherent rules and gives the backend clean section titles to use for citations.

### 6.2 Running Embeddings Locally with MiniLM
Instead of relying on an external embedding API, I used `all-MiniLM-L6-v2` running locally on CPU. For an HR policy assistant of this scale, generating embeddings locally takes only a couple of seconds, requires no extra API keys, eliminates rate limits during bulk document uploads, and keeps the ingestion flow self-contained. The 384-dimensional vectors are also lightweight, keeping memory footprint low and Chroma search fast.

### 6.3 Hybrid Search (Vector + BM25)
Employees search policy documents in two very different ways: some use casual phrasing like *"Can I roll over unused time off?"*, while others search for exact terms like *"LTA"*, *"Tier 2"*, or specific clause numbers. Dense vector search is great for understanding general intent, but it can miss exact acronyms or codes. BM25 catches those exact keywords effortlessly. Pairing both with an `EnsembleRetriever` ensures the system retrieves the right sections whether the question is paraphrased or uses exact policy jargon.

### 6.4 Two-Gate Grounding instead of Prompt-Only Guardrails
Telling an LLM *"only answer from context"* in the prompt is never 100% reliable—when given irrelevant or weak context, models often try to be helpful and invent plausible-sounding HR rules. To prevent this, I added two code-level checks: a similarity threshold check before calling the model that immediately returns a safe refusal if no policy matches, and a post-generation validation step that checks the returned citations against actual retrieved chunk metadata. This keeps hallucination prevention deterministic rather than relying solely on the model following instructions.

### 6.5 Note on Local LLMs (Ollama)
I considered adding a local LLM fallback using Ollama, but decided against it due to laptop hardware limitations. Running 7B/8B parameter models locally on my machine results in noticeable generation latency and lower reliability with strict Pydantic JSON schemas. To ensure fast response times and dependable citation extraction without incurring API costs, I chose to run embeddings locally with `all-MiniLM-L6-v2` and use Google Gemini's free tier for answer generation.

---

## 7. What I Would Improve With More Time

If I had more time to improve the system, I would focus on:

1. **Retrieval Evaluation Dataset:**
   Create a simple evaluation set of 30–40 realistic employee questions—including direct factual questions, acronyms, and questions with no answers in the policy. This would allow measuring how reliably the hybrid retriever pulls the right chunks and confirming that safe refusals trigger correctly.

2. **Handling Scanned or Image-Based PDFs:**
   The current setup expects digital PDFs with selectable text. If an HR policy is uploaded as a scanned document or contains clauses inside images, the parser cannot read it without OCR. Adding an OCR library (such as Tesseract) would make sure scanned documents are indexed properly.

3. **Document Versioning:**
   Currently, uploading a document with the same name replaces existing chunks. In real HR environments, policies update yearly (like *2025 vs. 2026 Benefits Guide*). Adding version numbers and effective dates to chunk metadata would prevent the system from returning answers from outdated policies.

4. **Handling Tables in PDFs:**
   HR policy PDFs often include tables for important details like leave allocations, health insurance tiers, and expense limits. Currently, the PDF parser does not extract table structures properly—it reads text as a flat stream, so rows and columns lose their relationships and get scrambled or split across chunks. Because of this, the assistant struggles to answer questions that rely on tabular data. Fixing this by adding layout-aware table parsing (converting tables into structured Markdown) will keep table rows together and ensure cells stay correctly related.

---