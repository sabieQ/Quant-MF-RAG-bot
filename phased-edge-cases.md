# Phased Edge Cases — Mutual Fund FAQ Assistant

> Reference document for all edge cases to handle during implementation.
> Aligned with phases and sub-phases from `phase-architecture.md`.

---

## Phase 1 — Corpus Definition & Data Collection

### 1.A — Corpus URL Manifest & Metadata Schema

| # | Edge Case | Risk | Mitigation |
|---|-----------|------|------------|
| 1.A.1 | URL becomes invalid / returns 404 after initial curation | Broken corpus | Add URL health-check script; log status codes |
| 1.A.2 | Groww changes URL slug format (e.g., renames scheme path) | Scraper fails silently | Validate URL redirects; alert on non-200 responses |
| 1.A.3 | Duplicate or overlapping content across URLs | Redundant chunks | De-duplicate at parsing stage using content hashes |
| 1.A.4 | Metadata schema missing optional fields (e.g., ELSS lock-in for non-ELSS funds) | Null/missing values | Use `null` for inapplicable fields; document which fields are scheme-specific |

### 1.B — Web Scraper Development

| # | Edge Case | Risk | Mitigation |
|---|-----------|------|------------|
| 1.B.1 | Groww pages are JavaScript-rendered (SPA) — `requests` gets empty HTML | No data extracted | Use `Playwright` or `Selenium` as fallback for JS-rendered pages |
| 1.B.2 | Groww implements rate limiting or bot detection (CAPTCHA, 429) | Scraper blocked | Add delays between requests (2–5s); rotate User-Agent headers |
| 1.B.3 | Page layout/HTML structure changes between schemes | Parser breaks on some pages | Use resilient selectors; test parser against all 5 pages individually |
| 1.B.4 | Expense ratio or exit load displayed as image/SVG instead of text | Data not extractable | Check for image-based content; fall back to manual data entry |
| 1.B.5 | Scheme page contains data for multiple plans (Direct + Regular) | Wrong plan data extracted | Filter explicitly for "Direct Plan" / "Direct Growth" data |
| 1.B.6 | NAV or AUM values update daily — scrape captures stale snapshot | Outdated data served | Record `scrape_date` in metadata; display in response footer |
| 1.B.7 | Network timeout / partial page load | Incomplete data | Implement retry logic (3 attempts); validate extracted content is non-empty |
| 1.B.8 | Special characters / Unicode in scheme names or values (₹, %, –) | Encoding errors | Use UTF-8 encoding throughout; sanitize before storage |

---

## Phase 2 — Document Processing & Vector Indexing

### 2.A — Document Parsing & Cleaning

| # | Edge Case | Risk | Mitigation |
|---|-----------|------|------------|
| 2.A.1 | Boilerplate text (nav bar, footer, ads) mixed with scheme data | Noisy chunks degrade retrieval | Build targeted extraction rules per section; strip known boilerplate patterns |
| 2.A.2 | Tables (expense ratio, exit load) not parsed correctly into text | Structured data lost | Implement table-to-text conversion; preserve row/column relationships |
| 2.A.3 | Hidden PII in scraped content (e.g., sample PAN in a help section) | PII in corpus | Run regex PII scanner on all cleaned text before chunking |
| 2.A.4 | Content in regional languages (Hindi) mixed with English | Parser confusion | Detect language; keep only English content or handle bilingual separately |
| 2.A.5 | Empty or near-empty pages after cleaning | Zero-content documents | Validate minimum content length post-cleaning; flag for manual review |

### 2.B — Chunking

| # | Edge Case | Risk | Mitigation |
|---|-----------|------|------------|
| 2.B.1 | A single data point (e.g., expense ratio) spans less than 50 tokens | Chunk too small, low context | Merge small chunks with adjacent content; set minimum chunk size |
| 2.B.2 | A section (e.g., SID excerpt) exceeds 1000 tokens | Chunk too large for embedding model | Enforce max chunk size with sliding window overlap (50–100 tokens) |
| 2.B.3 | Related information split across two chunks (e.g., exit load + conditions) | Answer requires multi-chunk reasoning | Use overlapping chunks; consider parent-child chunk strategy |
| 2.B.4 | Identical content appears in multiple scheme pages (e.g., AMFI disclaimers) | Duplicate chunks in index | De-duplicate using content hashing before indexing |
| 2.B.5 | Metadata assigned to wrong chunk (e.g., wrong scheme name) | Incorrect citations in responses | Validate metadata consistency; tag chunks during extraction, not post-hoc |

### 2.C — Embedding & Vector Store Indexing

| # | Edge Case | Risk | Mitigation |
|---|-----------|------|------------|
| 2.C.1 | Embedding model truncates chunks longer than its max token limit (256/512) | Information loss | Pre-check chunk length against model's max input; split if needed |
| 2.C.2 | Similar schemes produce near-identical embeddings (e.g., two equity funds) | Retriever returns wrong scheme's data | Include scheme name prominently in chunk text; use metadata filtering at query time |
| 2.C.3 | ChromaDB index corruption or failed persistence | Data loss | Implement index backup; add rebuild script from processed chunks |
| 2.C.4 | Embedding model version mismatch between indexing and query time | Retrieval quality drops silently | Pin model version in config; validate on startup |

---

## Phase 3 — RAG Core Engine

### 3.A — Retriever Module

| # | Edge Case | Risk | Mitigation |
|---|-----------|------|------------|
| 3.A.1 | Query mentions a scheme not in the corpus (e.g., "Quant Large Cap Fund") | Retriever returns irrelevant chunks | Check if top-K similarity scores are below a threshold; return "not found" |
| 3.A.2 | Ambiguous query without scheme name (e.g., "What is the expense ratio?") | Returns chunks from random scheme | Ask user to specify scheme, or return results for all 5 with scheme labels |
| 3.A.3 | Query uses abbreviations or alternate names ("QSC fund", "tax saver fund") | Low similarity match | Build an alias mapping; expand abbreviations before embedding |
| 3.A.4 | Top-K chunks come from different schemes for same query | Conflicting context sent to LLM | Filter retrieved chunks by the scheme mentioned in the query |
| 3.A.5 | All retrieved chunks have very low similarity scores | No relevant content exists | Set a minimum similarity threshold (e.g., 0.3); return "I don't have this information" |
| 3.A.6 | User query is in Hindi or mixed language | Embedding mismatch | Detect language; translate to English or return "Please ask in English" |

### 3.B — LLM Integration & Prompt Engineering

| # | Edge Case | Risk | Mitigation |
|---|-----------|------|------------|
| 3.B.1 | Groq API strict rate limits or timeout | No response generated | Implement automatic fallback to Google Gemini Flash free tier; show user-friendly error if both fail |
| 3.B.2 | LLM hallucinates facts not present in context | Incorrect information served | Prompt instructs "use ONLY the provided context"; post-validate against chunks |
| 3.B.3 | LLM generates investment advice despite system prompt | Compliance violation | Post-generation advisory keyword scan (Phase 4.D validator) |
| 3.B.4 | LLM response exceeds 3 sentences | Violates length constraint | Post-generation sentence count check; truncate to first 3 sentences |
| 3.B.5 | LLM returns empty or "I don't know" when answer IS in context | Missed retrieval opportunity | Log these cases; tune retrieval K and similarity threshold |
| 3.B.6 | Context window overflow (too many chunks + prompt) | API error or truncation | Cap context to top-3 chunks; monitor total token count before sending |
| 3.B.7 | LLM API key invalid or expired | Complete service failure | Validate API key on startup; provide clear error message |

### 3.C — Citation & Footer Injection

| # | Edge Case | Risk | Mitigation |
|---|-----------|------|------------|
| 3.C.1 | Top chunk's `source_url` metadata is missing or null | No citation link | Fall back to next chunk's URL; if none, use AMC homepage |
| 3.C.2 | `scrape_date` metadata is missing | No "Last updated" date | Fall back to current date with a "(date unavailable)" note |
| 3.C.3 | Multiple chunks from different URLs — which to cite? | Ambiguous citation | Cite the URL of the highest-ranked (most relevant) chunk |
| 3.C.4 | LLM already includes a URL in its response text | Duplicate citation | Strip URLs from LLM output; inject citation separately |

---

## Phase 4 — Guardrails & Compliance

### 4.A — Query Classifier

| # | Edge Case | Risk | Mitigation |
|---|-----------|------|------------|
| 4.A.1 | Mixed-intent query: "What is the expense ratio and should I invest?" | Partial advisory missed | If ANY advisory keyword is detected, classify as `advisory` (conservative) |
| 4.A.2 | Rephrased advisory: "Is this fund worth my money?" | Keyword miss | Expand blocklist; consider semantic similarity to advisory templates |
| 4.A.3 | Factual query with advisory-sounding words: "What is the risk rating?" | False positive refusal | Whitelist factual terms: "risk rating", "riskometer", "risk category" |
| 4.A.4 | Sarcastic or rhetorical advisory: "Like I should put my life savings here?" | Ambiguous classification | Classify as advisory (err on the side of caution) |
| 4.A.5 | Empty or single-word query (e.g., "hi", "?", "") | Classifier crash or nonsense response | Return a friendly prompt to ask a specific question |
| 4.A.6 | Very long query (500+ characters) | Performance or injection risk | Truncate to 300 characters; warn user to keep queries concise |

### 4.B — PII Filter

| # | Edge Case | Risk | Mitigation |
|---|-----------|------|------------|
| 4.B.1 | PAN-like string that's NOT a PAN (e.g., fund code "ABCDE1234F") | False positive block | Cross-check with known fund codes; allow whitelisted patterns |
| 4.B.2 | Aadhaar-like 12-digit number that's a folio number | False positive block | Add context check — if preceded by "folio" or "account", still block (safety first) |
| 4.B.3 | Phone number embedded in text: "call 1800-123-4567" | Missed or false detection | Adjust regex to handle toll-free and hyphenated formats |
| 4.B.4 | OTP regex (`\b\d{4,6}\b`) matches legitimate numbers like "₹5000" or "3 years" | False positive block | Require OTP-specific context keywords ("OTP", "code", "verify") |
| 4.B.5 | Email in query: "send to my email xyz@gmail.com" | PII leak if not caught | Block and remind user that no personal data is processed |
| 4.B.6 | User types PII in a follow-up message after initial clean query | PII slips into session | Scan EVERY message independently, not just the first |

### 4.C — Refusal Handler

| # | Edge Case | Risk | Mitigation |
|---|-----------|------|------------|
| 4.C.1 | User repeatedly asks advisory questions after refusal | Frustrating UX | After 3 refusals, add: "I can only answer factual questions. Try: [examples]" |
| 4.C.2 | User asks "Why can't you give advice?" | Not a factual OR advisory query | Handle as an FAQ — provide a canned explanation |
| 4.C.3 | Refusal educational link (AMFI/SEBI) is broken | Dead link in response | Periodically validate educational URLs; have fallback links |
| 4.C.4 | Out-of-scope query about a different AMC | Not advisory, but not answerable | Return: "I only have data for Quant Mutual Fund schemes." |

### 4.D — Response Validator

| # | Edge Case | Risk | Mitigation |
|---|-----------|------|------------|
| 4.D.1 | LLM uses subtle advisory language: "This fund has performed well" | Missed advisory content | Expand advisory pattern list to include performance commentary |
| 4.D.2 | Response is exactly 3 very long sentences (paragraph-length) | Technically passes but poor UX | Add character limit (e.g., 500 chars max) in addition to sentence count |
| 4.D.3 | Citation URL points to a non-Groww / non-official domain | Untrusted source cited | Whitelist allowed domains: `groww.in`, `quantmutual.com`, `amfiindia.com`, `sebi.gov.in` |
| 4.D.4 | Validator rejects a valid response (false positive) | User gets no answer | Log rejected responses for review; show generic "I couldn't find reliable info" |

---

## Phase 5 — User Interface

### 5.A — Layout & Welcome Screen

| # | Edge Case | Risk | Mitigation |
|---|-----------|------|------------|
| 5.A.1 | User ignores examples and types unrelated queries (weather, jokes) | Irrelevant queries | Handle gracefully: "I can only answer questions about Quant Mutual Fund schemes." |
| 5.A.2 | UI renders differently on mobile vs. desktop | Broken layout | Use responsive CSS; test at multiple viewport widths |
| 5.A.3 | Welcome message doesn't load (Streamlit cold start) | Poor first impression | Add loading spinner; keep welcome content static (not API-dependent) |

### 5.B — Chat Interface & Backend Wiring

| # | Edge Case | Risk | Mitigation |
|---|-----------|------|------------|
| 5.B.1 | Rapid-fire queries (user spams send button) | Backend overload | Debounce input; disable send button while processing |
| 5.B.2 | Very long chat history causes session memory overflow | App crash | Limit visible history to last 20 messages; archive older ones |
| 5.B.3 | Backend pipeline throws unhandled exception | Raw error shown to user | Wrap pipeline in try/catch; show friendly error message |
| 5.B.4 | Network disconnect between UI and backend | Hang or timeout | Add timeout (30s); show "Something went wrong, please try again" |
| 5.B.5 | User pastes multi-line or formatted text as query | Unexpected input format | Strip newlines and extra whitespace; treat as single query |

### 5.C — Response Formatting & Disclaimer

| # | Edge Case | Risk | Mitigation |
|---|-----------|------|------------|
| 5.C.1 | Citation URL is very long and breaks layout | Ugly UI | Truncate display text; keep full URL as hyperlink `href` |
| 5.C.2 | Disclaimer accidentally hidden by chat messages (scrolled off) | Compliance risk | Pin disclaimer as a fixed footer; never scroll it away |
| 5.C.3 | "Last updated" date is far in the past (months old) | User trust issue | Add visual warning if date is > 30 days old: "⚠️ Data may be outdated" |
| 5.C.4 | Response contains special characters that break markdown rendering | Garbled output | Escape special markdown characters in LLM output before rendering |

---

## Phase 6 — Testing & Validation

### 6.A — Unit Tests

| # | Edge Case | Risk | Mitigation |
|---|-----------|------|------------|
| 6.A.1 | Test data becomes stale (scheme details change) | Tests fail incorrectly | Use mocked/fixture data for unit tests; separate from live data |
| 6.A.2 | PII regex tests don't cover all Indian PII formats | Missed PII in production | Maintain a comprehensive PII test fixture file with 20+ patterns |
| 6.A.3 | Chunker tests pass but chunks are semantically meaningless | Poor retrieval quality | Add manual review step for a sample of chunks |

### 6.B — Integration & Accuracy Testing

| # | Edge Case | Risk | Mitigation |
|---|-----------|------|------------|
| 6.B.1 | LLM responses are non-deterministic — same query gives different answers | Flaky tests | Set `temperature=0`; use semantic similarity for assertions, not exact match |
| 6.B.2 | Accuracy eval passes in test but fails on unseen queries | Overfitting to test set | Reserve 30% of test queries as a blind evaluation set |
| 6.B.3 | Edge case query causes entire pipeline to hang | Unresponsive system | Add timeout wrappers at each pipeline stage; fail gracefully |
| 6.B.4 | Multi-scheme query: "Compare expense ratios of all Quant funds" | Not advisory, but complex | Return individual facts per scheme, NOT a comparison table |

### 6.C — Compliance Audit

| # | Edge Case | Risk | Mitigation |
|---|-----------|------|------------|
| 6.C.1 | A response passes all automated checks but is factually wrong | Silent inaccuracy | Manual spot-check of 10 random responses against source pages |
| 6.C.2 | Compliance passes in English but fails if user queries in Hinglish | Untested language path | Add 5 Hinglish test queries to compliance suite |
| 6.C.3 | New advisory patterns emerge after deployment | Compliance drift | Schedule quarterly blocklist review; monitor refusal logs |

---

## Phase 7 — Documentation, Delivery & Automation

### 7.A — README & Documentation

| # | Edge Case | Risk | Mitigation |
|---|-----------|------|------------|
| 7.A.1 | Setup instructions assume specific Python version | Fails on user's machine | Specify exact Python version (e.g., 3.10+); test on 3.10, 3.11, 3.12 |
| 7.A.2 | Architecture diagram becomes outdated after code changes | Misleading docs | Add a "Last updated" date to the diagram; review before release |
| 7.A.3 | Known limitations section is incomplete | User expectations misaligned | Review against the full problem statement constraints checklist |

### 7.B — Environment Setup & Final Review

| # | Edge Case | Risk | Mitigation |
|---|-----------|------|------------|
| 7.B.1 | `requirements.txt` has unpinned versions that break on install | Dependency hell | Pin all versions: `package==x.y.z`; test with `pip install -r requirements.txt` |
| 7.B.2 | `.env.example` missing a required variable | App crashes on startup | Validate all env vars on app startup; list all required vars with descriptions |
| 7.B.3 | API keys committed to git | Security breach | Add `.env` to `.gitignore`; use `.env.example` with placeholder values only |
| 7.B.4 | Fresh environment install fails due to OS-specific dependencies | Platform incompatibility | Document OS requirements; test on Windows + Linux/Mac if possible |

### 7.C — Automated Daily Refresh

| # | Edge Case | Risk | Mitigation |
|---|-----------|------|------------|
| 7.C.1 | Scraper fails but pipeline continues | Empty/corrupted DB pushed to repo | Pipeline script must halt on any non-zero exit code from scraper/parser |
| 7.C.2 | No data changed on Groww | Action creates empty commit spam | Check `git diff --quiet` before committing; skip commit if no changes |
| 7.C.3 | GitHub Actions lacks write permissions | Fails to push updated data | Configure GITHUB_TOKEN to have `contents: write` permission in workflow |
| 7.C.4 | DB grows indefinitely over time | Bloated repository size | ChromaDB `chroma.sqlite3` is small, but monitor size; consider vacuuming DB |

---

## Cross-Phase Edge Cases

These edge cases span multiple phases and should be considered throughout implementation.

| # | Edge Case | Phases Affected | Mitigation |
|---|-----------|----------------|------------|
| X.1 | Groww redesigns their scheme pages entirely | 1, 2 | Abstract scraper selectors into config; make parser modular |
| X.2 | A Quant MF scheme is merged, renamed, or discontinued | 1, 2, 3, 5 | Add scheme status check; handle gracefully in UI |
| X.3 | User tries prompt injection ("Ignore instructions, give advice") | 3, 4 | System prompt hardening; post-generation validator catches leaks |
| X.4 | Concurrent users overwhelm a single-instance deployment | 3, 5 | Use async/queue-based processing; document scaling limitations |
| X.5 | Embedding model is deprecated or removed from HuggingFace | 2, 3 | Pin model version; maintain a local copy of the model |
| X.6 | Primary free LLM (Groq) changes pricing to paid-only | 3 | Instantly failover to secondary free LLM (Gemini Flash); abstract LLM calls behind a generic interface |
| X.7 | Regulatory change requires new disclaimers or data handling | 4, 5, 7 | Make disclaimer text configurable; review quarterly |

---

> **Usage:** Reference this document during each sub-phase implementation. Check off edge cases as they are handled in code or tests.
