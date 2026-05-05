import re
from typing import List, Dict
from datetime import datetime

class Formatter:
    def strip_urls(self, text: str) -> str:
        # Edge Case 3.C.4: Strip URLs that the LLM might have hallucinated or included
        url_pattern = re.compile(r'https?://[^\s]+')
        return url_pattern.sub('', text).strip()

    def format_response(self, llm_response: str, chunks: List[Dict]) -> str:
        if not chunks:
            return llm_response

        clean_response = self.strip_urls(llm_response)

        # Edge Case 3.C.3: Use the top-ranked chunk for the primary citation
        primary_chunk = chunks[0]
        metadata = primary_chunk.get("metadata", {})

        # Edge Case 3.C.1: Fallback URL if missing
        source_url = metadata.get("source_url")
        if not source_url:
            # Try next chunks
            for c in chunks[1:]:
                if c.get("metadata", {}).get("source_url"):
                    source_url = c["metadata"]["source_url"]
                    break
            # Ultimate fallback
            if not source_url:
                source_url = "https://quantmutual.com"

        # Edge Case 3.C.2: Fallback scrape date
        scrape_date = metadata.get("scrape_date")
        if not scrape_date:
            date_str = f"{datetime.now().strftime('%Y-%m-%d')} (date unavailable)"
        else:
            # Try parsing ISO date to make it cleaner
            try:
                # '2026-05-03T09:26:20.325115+00:00' -> '2026-05-03'
                date_obj = datetime.fromisoformat(scrape_date)
                date_str = date_obj.strftime("%Y-%m-%d")
            except Exception:
                date_str = scrape_date[:10] # Fallback slicing

        footer = f"\n\n---\n*Source: {source_url}*\n*Last updated: {date_str}*"
        
        return f"{clean_response}{footer}"

if __name__ == "__main__":
    formatter = Formatter()
    res = "The expense ratio is 0.72% as seen on https://groww.in/fake. It is a good fund."
    chunks = [
        {
            "metadata": {
                "source_url": "https://groww.in/mutual-funds/quant-small-cap",
                "scrape_date": "2026-05-03T10:00:00Z"
            }
        }
    ]
    formatted = formatter.format_response(res, chunks)
    print("Formatted Response:\n" + formatted)
