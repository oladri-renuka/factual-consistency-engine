import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

# Database paths
DB_PATH = PROJECT_ROOT / "data" / "fact_ledger.db"
ANNOTATIONS_DB_PATH = PROJECT_ROOT / "data" / "annotations.db"

# Model configurations
NLI_MODEL = "microsoft/deberta-v3-large"
CLAIM_EXTRACTOR_MODEL = "microsoft/deberta-v3-base"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# API configurations
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "anthropic/claude-3.5-sonnet"
OPENROUTER_BASE_URL = "https://openrouter.io/api/v1"

# Contradiction thresholds
CONTRADICTION_THRESHOLD = 0.7
SIMILARITY_THRESHOLD = 0.75

# Generation parameters
MAX_TOKENS = 2000
TEMPERATURE = 0.7

# Evaluation
BATCH_SIZE_GENERATION = 10
NUM_EVALUATION_REPORTS = 100
NUM_ANNOTATORS = 2

# Data directories
DATA_DIR = PROJECT_ROOT / "data"
MODELS_DIR = PROJECT_ROOT / "models"
RESULTS_DIR = PROJECT_ROOT / "results"
ANNOTATIONS_DIR = PROJECT_ROOT / "annotations"

for dir_path in [DATA_DIR, MODELS_DIR, RESULTS_DIR, ANNOTATIONS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)
