# Factual Consistency Engine for Long-Form Generation

A real-time contradiction detection and fixing system for LLM-generated financial earnings reports using a fact ledger architecture.

## Architecture Overview

### Core Components

1. **Fact Ledger** (`fact_ledger.py`)
   - SQLite-based database storing extracted claims with embeddings
   - Schema: claims (id, text, embedding, paragraph_number, confidence), documents, contradictions
   - Real-time claim storage and retrieval during generation

2. **Claim Extractor** (`claim_extractor.py`)
   - Fine-tuned DeBERTa-v3-base for identifying factual claims in text
   - Confidence scoring for each extracted claim
   - Batch processing support

3. **Embeddings** (`embeddings.py`)
   - Sentence-transformers (all-MiniLM-L6-v2) for semantic representation
   - Similarity computation for claim matching
   - Batch similarity calculations

4. **Contradiction Detector** (`contradiction_detector.py`)
   - microsoft/deberta-v3-large NLI model
   - Bidirectional contradiction checking
   - Contradiction probability > 0.7 triggers regeneration

5. **Report Generator** (`report_generator.py`)
   - Claude Sonnet 3.5 via OpenRouter API
   - Real-time contradiction detection during generation
   - Fact ledger constraint enforcement

### Frontend & APIs

- **Gradio Interface** (`gradio_interface.py`)
  - Side-by-side comparison: generated vs. baseline
  - Contradiction highlighting
  - Real-time company input with financial metrics

- **FastAPI** (`api.py`)
  - POST `/generate` - Generate earnings reports with contradiction detection
  - GET `/document/{document_id}` - Retrieve document claims and contradictions
  - GET `/health` - Service health check

## Evaluation Framework

### Dataset Generation
- **100 synthetic earnings reports** with realistic financial data
- Companies: TechCorp Inc., DataFlow Systems, CloudNine Solutions, etc.
- Segments: Technology, Finance, Healthcare, Retail, Manufacturing

### Human Annotation
- **Label Studio integration** (`annotation_manager.py`)
- **2 annotators** per report for inter-annotator agreement
- Binary classification: contradiction vs. non-contradiction

### Metrics
- **Precision & Recall** - Contradiction detection accuracy
- **Cohen's Kappa** - Inter-annotator agreement coefficient
- **F1 Score** - Harmonic mean of precision/recall
- **Contradiction Reduction %** - vs. baseline

## Installation

```bash
pip install -r requirements.txt
```

### Environment Setup
```bash
export OPENROUTER_API_KEY="your-openrouter-api-key"
```

## Usage

### 1. Gradio Interface
```bash
python gradio_interface.py
```
Opens at http://localhost:7860

### 2. FastAPI Server
```bash
python api.py
```
Available at http://localhost:8000

**Example Request:**
```bash
curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "TechCorp Inc.",
    "financial_data": {
      "revenue_current": 1000000,
      "revenue_previous": 900000,
      "net_income": 150000,
      "growth_rate": 11.1,
      "employees": 500
    },
    "check_contradictions": true
  }'
```

### 3. Generate Evaluation Dataset
```bash
python evaluation_dataset.py
```
Generates 100 earnings reports in `results/evaluation_dataset/`

### 4. Run Evaluation
```bash
python run_evaluation.py
```
Produces:
- Inter-annotator agreement (Cohen's kappa)
- Precision/recall metrics
- Contradiction detection report

## Fact Ledger Architecture

### Generation Flow

```
1. Extract claims from each paragraph
   ↓
2. Store in SQLite with embeddings
   ↓
3. Before generating next paragraph:
   - Extract candidate sentences
   - Compare embeddings (similarity > 0.75)
   ↓
4. If DeBERTa contradiction prob > 0.7:
   - Regenerate that paragraph with ledger as constraint
   - Or flag as need-human-review
   ↓
5. Accept claims, add to ledger, continue
```

### Database Schema

**claims table:**
- id (PRIMARY KEY)
- document_id (FK → documents)
- paragraph_number
- claim_text
- embedding (binary blob)
- confidence (0.0-1.0)
- created_at (timestamp)

**contradictions table:**
- id (PRIMARY KEY)
- document_id (FK → documents)
- claim_id_1, claim_id_2 (FK → claims)
- contradiction_score (0.0-1.0)
- detected_at (timestamp)

## Models Used

| Component | Model | Source |
|-----------|-------|--------|
| NLI (Contradiction) | microsoft/deberta-v3-large | HuggingFace |
| Claim Extraction | microsoft/deberta-v3-base | HuggingFace |
| Embeddings | sentence-transformers/all-MiniLM-L6-v2 | Sentence Transformers |
| Generation | claude-sonnet-4 | OpenRouter |

## Key Configuration Parameters

| Parameter | Value | Purpose |
|-----------|-------|---------|
| `CONTRADICTION_THRESHOLD` | 0.7 | Triggers regeneration if exceeded |
| `SIMILARITY_THRESHOLD` | 0.75 | For finding semantically similar claims |
| `MAX_TOKENS` | 2000 | Report generation length |
| `TEMPERATURE` | 0.7 | Generation temperature (0.0-1.0) |
| `NUM_EVALUATION_REPORTS` | 100 | Dataset size |
| `NUM_ANNOTATORS` | 2 | Inter-annotator agreement |

## Output Examples

### Generated Report
```
TechCorp Inc. reported revenue of $1M in Q4, up 11.1% YoY from $900K.
Operating margin improved to 15%, with net income of $150K.
The company serves the Technology segment with products including
Cloud Platform, API Gateway, and Data Analytics.
```

### Contradiction Detection
```
Claim 1: "Revenue increased 11.1% YoY"
Claim 2: "Revenue growth was modest at 3%"
Contradiction Score: 0.89
Paragraph: 2
Status: CAUGHT & FLAGGED
```

## Results Directory Structure

```
results/
├── evaluation_dataset/
│   ├── report_001.json
│   ├── report_002.json
│   └── metadata.json
├── evaluation_dataset.json
└── evaluation_results.json
```

## Best Practices

1. **API Key Management**: Use environment variables, never hardcode
2. **Batch Processing**: Use batch methods for multiple reports
3. **Database Cleanup**: Call `.close()` on ledger and managers
4. **Contradiction Checking**: Always enable for production
5. **Ground Truth**: Human annotations are critical for evaluation

## Limitations & Future Work

- Sentence-level contradictions only (no multi-sentence reasoning)
- No cross-document contradiction checking
- Regeneration via re-prompting (not iterative refinement)
- No domain-specific fine-tuning of NLI model
- Label Studio UI requires manual setup

## References

- DeBERTa: https://huggingface.co/microsoft/deberta-v3-large
- Sentence Transformers: https://www.sbert.net/
- Cohen's Kappa: https://en.wikipedia.org/wiki/Cohen%27s_kappa
- OpenRouter: https://openrouter.io/

## License

MIT
