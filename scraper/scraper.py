import json
import time
import requests
import logging
from datetime import datetime, timezone
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_scraper(manifest_path="corpus_urls.json"):
    base_dir = Path(__file__).parent.parent
    manifest_file = base_dir / "scraper" / manifest_path
    raw_dir = base_dir / "data" / "raw"
    metadata_file = base_dir / "scraper" / "source_metadata.json"
    
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except FileNotFoundError:
        logging.error(f"Manifest not found at {manifest_file}")
        return

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9'
    }

    metadata_list = []

    for item in manifest:
        scheme_id = item["id"]
        url = item["url"]
        scheme_name = item["scheme_name"]
        category = item["category"]
        
        logging.info(f"Scraping {scheme_name}...")
        
        try:
            # Mitigation for 1.B.2: Delay and headers
            time.sleep(2)
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            # Mitigation for 1.B.8: Force UTF-8 encoding if not set
            response.encoding = 'utf-8'
            html_content = response.text
            
            # Save raw HTML
            raw_file_path = raw_dir / f"{scheme_id}.html"
            with open(raw_file_path, "w", encoding="utf-8") as rf:
                rf.write(html_content)
                
            scrape_date = datetime.now(timezone.utc).isoformat()
            
            # Build metadata
            meta = {
                "scheme_id": scheme_id,
                "source_url": url,
                "scheme_name": scheme_name,
                "category": category,
                "document_type": "HTML",
                "scrape_date": scrape_date,
                "elss_lock_in": "3 Years" if category == "ELSS" else None
            }
            metadata_list.append(meta)
            
            logging.info(f"Saved {scheme_id}.html successfully.")
            
        except Exception as e:
            logging.error(f"Failed to scrape {url}: {e}")

    # Save metadata
    with open(metadata_file, "w", encoding="utf-8") as mf:
        json.dump(metadata_list, mf, indent=2, ensure_ascii=False)
    
    logging.info(f"Scraping complete. Metadata saved to {metadata_file}")

if __name__ == "__main__":
    run_scraper()
