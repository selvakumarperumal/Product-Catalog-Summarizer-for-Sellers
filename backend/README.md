# Product Catalog Summarizer for Sellers

A clean, production-ready Generative AI service for summarizing e-commerce product catalogs using Google Gemini LLM and FastAPI.

## Structure

```
backend/
├── app/
│   ├── main.py                  # FastAPI application entry point
│   ├── config.py                # Environment configuration (Pydantic Settings)
│   ├── core/
│   │   ├── logging_config.py    # Console logging setup
│   │   └── exceptions.py        # Custom exception hierarchy & FastAPI handlers
│   ├── prompts/                 # Prompt engineering module
│   │   ├── templates.py         # ChatPromptTemplates loading from prompts.yaml
│   │   ├── few_shot.py          # In-context few-shot example formatter
│   │   └── chains.py            # LCEL prompt chains (summarize & review)
│   ├── services/
│   │   ├── llm_service.py       # Gemini Chat model, LCEL pipeline & retry logic
│   │   └── file_service.py      # CSV/XLSX reader, upload validator & chunker
│   ├── models/
│   │   └── schemas.py           # Pydantic request/response models & LLM schemas
│   └── api/
│       └── routes.py            # API routes (/upload, /summarize, /download, /health)
├── config/
│   ├── logging.yaml             # Console logging settings
│   └── prompts.yaml             # Externalized prompt templates & few-shot examples
├── uploads/                     # Staged uploaded files
├── output/                      # Summarization output CSV files
└── requirements.txt             # Pip dependencies
```

## Running the Application

### 1. Environment Variables
Make sure your environment variable `TF_GOOGLE_API_KEY` is set (e.g. via `.envrc` or direnv):
```bash
export TF_GOOGLE_API_KEY="your-gemini-api-key"
export TF_MODEL_NAME="gemini-2.0-flash"
export TF_MODEL_TEMPERATURE="0.3"
```

### 2. Run Server
```bash
uvicorn app.main:app --reload
```

## API Usage

### Summarize a Product Catalog (single call)
```bash
curl -X POST "http://localhost:8000/api/v1/summarize" \
  -F "file=@/path/to/product_catalog.csv" \
  -o summarized_output.csv
```
*Upload a CSV/XLSX file and receive the summarized CSV directly as a downloadable response.*
