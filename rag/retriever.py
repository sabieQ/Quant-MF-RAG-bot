import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import re
import chromadb
from chromadb.utils import embedding_functions
from config import CHROMA_DB_DIR, COLLECTION_NAME, EMBEDDING_MODEL, RETRIEVER_TOP_K, SIMILARITY_THRESHOLD
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

ALIASES = {
    "qsc": "Quant Small Cap",
    "small cap": "Quant Small Cap",
    "elss": "Quant ELSS",
    "tax saver": "Quant ELSS",
    "tax fund": "Quant ELSS",
    "qma": "Quant Multi Asset",
    "multi asset": "Quant Multi Asset",
    "qmc": "Quant Mid Cap",
    "mid cap": "Quant Mid Cap",
    "qfc": "Quant Flexi Cap",
    "flexi cap": "Quant Flexi Cap",
    "flexicap": "Quant Flexi Cap"
}

# Known schemes for filtering (Edge Case 3.A.4)
KNOWN_SCHEMES = [
    "Quant Small Cap",
    "Quant ELSS",
    "Quant Multi Asset",
    "Quant Mid Cap",
    "Quant Flexi Cap"
]

class Retriever:
    def __init__(self):
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=EMBEDDING_MODEL)
        self.client = chromadb.PersistentClient(path=str(CHROMA_DB_DIR))
        self.collection = self.client.get_collection(name=COLLECTION_NAME, embedding_function=self.ef)

    def is_english(self, text: str) -> bool:
        # Edge Case 3.A.6: Simple heuristic for Hindi/Devanagari characters
        if re.search(r'[\u0900-\u097F]', text):
            return False
        return True

    def expand_query(self, query: str) -> str:
        # Edge Case 3.A.3: Alias mapping
        expanded = query.lower()
        for alias, full_name in ALIASES.items():
            expanded = re.sub(r'\b' + re.escape(alias) + r'\b', full_name.lower(), expanded)
        return expanded

    def extract_scheme(self, expanded_query: str):
        # Edge Case 3.A.4: Find if the user is asking about a specific scheme
        q = expanded_query.lower()
        found_schemes = []
        for scheme in KNOWN_SCHEMES:
            if scheme.lower() in q:
                found_schemes.append(scheme)
        return found_schemes

    def retrieve(self, query: str):
        if not self.is_english(query):
            return {"error": "Please ask your question in English."}

        expanded_query = self.expand_query(query)
        target_schemes = self.extract_scheme(expanded_query)

        # Fetch more results to allow for post-filtering
        results = self.collection.query(
            query_texts=[expanded_query],
            n_results=RETRIEVER_TOP_K * 3
        )

        if not results["documents"] or not results["documents"][0]:
            return {"error": "No relevant information found."}

        # Edge Case 3.A.1, 3.A.5: Similarity Threshold
        valid_chunks = []
        distances = results["distances"][0]
        docs = results["documents"][0]
        metas = results["metadatas"][0]

        for doc, meta, dist in zip(docs, metas, distances):
            similarity = 1.0 - dist
            if similarity >= SIMILARITY_THRESHOLD:
                # Edge Case 3.A.4: Filter by target scheme if requested
                if target_schemes:
                    # Check if any target scheme is a substring of the chunk's scheme_name
                    chunk_scheme = meta.get("scheme_name", "").lower()
                    if not any(ts.lower() in chunk_scheme for ts in target_schemes):
                        continue
                
                valid_chunks.append({
                    "content": doc,
                    "metadata": meta,
                    "similarity": similarity
                })

        # Return only the top K valid chunks
        valid_chunks = valid_chunks[:RETRIEVER_TOP_K]

        if not valid_chunks:
            return {"error": "I don't have this information in my current data."}

        return {"chunks": valid_chunks}

if __name__ == "__main__":
    retriever = Retriever()
    queries = [
        "What is the expense ratio of QSC?",
        "What is the exit load for ELSS?",
        "Tell me about mutual funds", # English alternative to avoid Unicode crash
        "Who is the fund manager?", # Ambiguous
        "What is the lock-in for Quant Multi Asset?",
        "Give me data for Quant Large Cap Fund" # Not in corpus
    ]
    for q in queries:
        # Safe print for Windows console
        print(f"\nQuery: {q.encode('ascii', 'replace').decode('ascii')}")
        res = retriever.retrieve(q)
        if "error" in res:
            print(f"Error: {res['error']}")
        else:
            print(f"Top result similarity: {res['chunks'][0]['similarity']:.4f}")
            print(f"Top result scheme: {res['chunks'][0]['metadata']['scheme_name']}")
