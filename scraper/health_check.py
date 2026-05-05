import json
import requests
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_urls(file_path="corpus_urls.json"):
    """
    Reads URLs from corpus manifest and checks their health.
    Handles Edge Cases 1.A.1 (404/invalid) and 1.A.2 (Redirects/non-200).
    """
    file_path = Path(__file__).parent / file_path
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
    except FileNotFoundError:
        logging.error(f"Manifest file not found: {file_path}")
        return False

    all_healthy = True
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    for item in manifest:
        url = item["url"]
        scheme = item["scheme_name"]
        logging.info(f"Checking URL for {scheme}: {url}")
        
        try:
            # We use allow_redirects=True to catch redirects
            response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
            
            if response.status_code == 200:
                if response.history:
                    logging.warning(f"URL Redirected! Original: {url}, Final: {response.url} (Edge Case 1.A.2)")
                else:
                    logging.info("Status: OK (200)")
            else:
                logging.error(f"Status: FAILED ({response.status_code}) (Edge Case 1.A.1/1.A.2)")
                all_healthy = False
                
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed: {e} (Edge Case 1.A.1)")
            all_healthy = False
            
    return all_healthy

if __name__ == "__main__":
    logging.info("Starting corpus URL health check...")
    success = check_urls()
    if success:
        logging.info("All URLs are healthy.")
    else:
        logging.error("Some URLs failed the health check.")
