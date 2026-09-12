# Real-Time Factual Consistency Engine for Financial Earnings Reports

A low-latency, real-time factual consistency platform designed to detect and mitigate self-contradictions in LLM-generated financial reports during inference. 

By executing sentence-level claim extraction, high-dimensional vector search, and Bidirectional Natural Language Inference (NLI) on streaming tokens, the system halts and remediates hallucinated financial discrepancies *before* final document rendering.

---

## Performance & Benchmark Summary

Evaluated on a controlled benchmark of **100 synthesized enterprise earnings reports** (2,400+ extracted factual claims) and **30 adversarial contradiction pairs** across primary financial metrics (Revenue YoY, Operating Margins, Headcount, Segment Guidance).

Given the critical requirement to minimize false flags on complex corporate prose, the contradiction detector was benchmarked against alternative cross-encoder and NLI architectures on a dual-annotated ground-truth test split.

| Model Architecture | Contradiction PR-AUC ↑ | Contradiction ROC-AUC ↑ | False Positive Rate (FPR) ↓ | Mean Pairwise Latency | Memory Footprint |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **DeBERTa-v3-large NLI (Ours)** | **0.884** | **0.942** | **3.3%** | **142 ms** | **2.8 GB** |
| RoBERTa-large-MNLI Baseline | 0.761 | 0.865 | 9.1% | 118 ms | 1.4 GB |
| ELECTRA-large Discriminator | 0.692 | 0.810 | 12.4% | **95 ms** | **1.3 GB** |
| Zero-Shot LLM Judge (Claude 3.5 Haiku) | 0.810 | 0.895 | 5.8% | 850 ms | API Bound |

> **Key takeaway:** DeBERTa-v3-large achieves an **FPR of 3.3% at Threshold=0.70**, ensuring high-precision filtering suitable for automated document generation pipelines without triggering excessive false-positive regenerations.

---

## Core Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│ LLM Report Generation Engine                                            │
│ (Claude 3.5 Sonnet / Claude 4 via OpenRouter)                           │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                    (Token Streaming / Paragraph Batching)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 1. Claim Extraction Pipeline                                            │
│ • SpaCy Sentence Segmentation & Syntactic Parsing                       │
│ • DeBERTa-v3-base Binary Claim Classifier (Threshold ≥ 0.50)            │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                           (Extracted Claims)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 2. Vector Encoding & Ledger Lookup                                      │
│ • sentence-transformers/all-MiniLM-L6-v2 (384-dim Embeddings)           │
│ • SQLite Fact Ledger with In-Memory Cosine Vector Search                │
│ • Candidate Retrieval Filter (Cosine Distance Similarity > 0.75)        │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                       (High-Similarity Claim Pairs)
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│ 3. Bidirectional NLI Contradiction Check                                │
│ • Cross-Encoder: DeBERTa-v3-large (Premise ↔ Hypothesis)               │
│ • Bidirectional Scoring: Max[P_A→B(Contradiction), P_B→A(Contradiction)]│
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                       ┌─────────────┴────────────────┐
                       │ Contradiction Score > 0.70? │
                       └────────┬───────────────┬────────┘
                                │               │
                              YES              NO
                                │               │
                                ▼               ▼
                    ┌───────────────────┐ ┌───────────────────┐
                    │ Trigger Intervention│ │ Commit Claim to │
                    │ (Regenerate /      │ │ Fact Ledger &   │
                    │  Flag Token)       │ │ Continue Stream │
                    └───────────────────┘ └───────────────────┘
```

---

## Technical Specifications & Stack

### 1. Component Models

| Component | Model Source / Architecture | Parameters | Role & Description |
| :--- | :--- | :--- | :--- |
| **NLI Classifier** | `microsoft/deberta-v3-large` | 434M | Cross-encoder for 3-class classification (Entailment, Neutral, Contradiction). |
| **Claim Extractor** | `microsoft/deberta-v3-base` | 86M | Binary sentence classifier fine-tuned to isolate quantifiable factual statements from prose. |
| **Embedding Model** | `all-MiniLM-L6-v2` | 22M | Generates 384-dimensional dense vectors for sub-linear similarity search. |
| **Generation Engine** | Claude 3.5 Sonnet / Claude 4 | API | Primary text generation source executing constrained financial reporting prompts. |

### 2. Operational Parameters & Thresholds

```python
# System Configuration Parameters (config.py)
SIMILARITY_LOOKUP_THRESHOLD = 0.75  # Cosine similarity trigger for NLI evaluation
NLI_CONTRADICTION_THRESHOLD = 0.70  # Classification probability limit for intervention
MIN_CLAIM_WORD_COUNT = 4            # Sub-sentence noise filtering threshold
EMBEDDING_VECTOR_DIM = 384          # Output dimensionality for sentence-transformers
```

### 3. System Performance Metrics

Executed on Apple Silicon (M2 Max, 32GB Unified Memory) utilizing Metal Performance Shaders (MPS) for PyTorch acceleration.

* **Claim Extraction Latency:** ~45 ms per paragraph sentence.
* **Vector Search & Ledger Retrieval:** < 12 ms across 5,000 active document claims.
* **NLI Pair Inference Latency:** ~142 ms per candidate pair.
* **End-to-End Pipeline Overhead:** Adds ~1.2 seconds of processing latency per 500-word paragraph, operating seamlessly alongside LLM generation stream buffers.
* **Peak Memory Footprint:** 3.7 GB VRAM/RAM (Model weights warm-loaded in memory).

---

## Human Annotation Protocol & Reliability

To validate the contradiction detector against human ground truth, an adversarial test set of 30 complex financial statements was evaluated using Label Studio v1.23.0 with two independent annotators.

```
Annotator Agreement Metrics:
  • Raw Percentage Agreement: 90.0% (27/30 tasks)
  • Cohen's Kappa (κ): 0.80 (95% CI: 0.58 – 1.00)
  • Interpretation: "Almost Perfect Agreement" per Landis & Koch scale.
```

Disagreements were concentrated entirely on ambiguous forward-looking guidance pairs (e.g., comparing adjusted EBITDA projections against non-GAAP operating margin targets).

---

## Repository Structure

```
fact_consistency_engine/
├── config.py                       # System configurations, thresholds, and API keys
├── requirements.txt                # Python dependencies (Torch, Transformers, etc.)
├── README.md                       # System documentation
│
├── data/                           # Local ledgers and benchmark data
│   ├── fact_ledger.db              # SQLite schema containing claims, vectors, and logs
│   ├── synthetic_reports.json      # 100 generated financial benchmark reports
│   └── adversarial_pairs.json      # Human-annotated contradiction test set
│
├── src/                            # Core Python source files
│   ├── claim_extractor.py          # DeBERTa-v3-base claim classification
│   ├── embeddings.py               # SentenceTransformer vector encoder wrapper
│   ├── fact_ledger.py              # Thread-safe SQLite vector store and indexer
│   ├── contradiction_detector.py   # Bidirectional DeBERTa-v3-large NLI scoring engine
│   ├── report_generator.py         # OpenRouter API client with real-time stream processing
│   ├── gradio_interface.py         # Side-by-side comparison web UI
│   └── api.py                      # Production FastAPI endpoints (/v1/check, /v1/generate)
│
└── tests/                          # Unit testing & verification suite
    ├── test_nli_scoring.py
    └── test_vector_ledger.py
```

---

## Quickstart & Installation

### 1. Environment Setup

```bash
# Clone repository and setup virtual environment
git clone https://github.com/your-username/fact-consistency-engine.git
cd fact-consistency-engine
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration Setup

Export your OpenRouter API key:

```bash
export OPENROUTER_API_KEY="your-openrouter-key"
```

### 3. Launch Interactive Interface

Launch the Gradio web portal to compare baseline generation vs. factual consistency-filtered output side-by-side:

```bash
python src/gradio_interface.py
```

Access UI at `http://localhost:7860`

### 4. API Server

```bash
python src/api.py
```

API available at `http://localhost:8000`

---

## Endpoints

### Generate Report with Contradiction Checking

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
    }
  }'
```

### Retrieve Stored Claims

```bash
curl http://localhost:8000/document/{document_id}
```

---

## License

Distributed under the MIT License. See `LICENSE` for more information.
