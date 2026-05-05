import os
from pathlib import Path

# Base Paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
CHROMA_DB_DIR = DATA_DIR / "chroma_db"

# Vector Store Settings
COLLECTION_NAME = "quant_mf_faq"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Retriever Settings
RETRIEVER_TOP_K = 5
SIMILARITY_THRESHOLD = 0.15  # Lower threshold for all-MiniLM-L6-v2
