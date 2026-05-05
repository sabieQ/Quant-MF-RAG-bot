import os
import re
from typing import List, Dict
import logging
from dotenv import load_dotenv

try:
    from groq import Groq
except ImportError:
    Groq = None

try:
    from google import genai
except ImportError:
    genai = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
load_dotenv()

PROMPT_TEMPLATE = """You are a facts-only mutual fund FAQ assistant for Quant Mutual Fund.
Answer the user's question using ONLY the provided context below.
Do NOT give investment advice, opinions, or recommendations.
Limit your answer to 3 sentences maximum.

CONTEXT:
{context}

RULES:
1. Answer in 3 sentences or less using ONLY the context above. (Edge Case 3.B.2)
2. If the context does not contain the answer, reply exactly with: "I don't have this information in my current data."
3. Do NOT recommend, compare, or advise.

USER QUESTION: {query}"""

class Generator:
    def __init__(self):
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")

        # Edge Case 3.B.7: Validate API keys on startup
        if not self.groq_api_key and not self.gemini_api_key:
            logging.error("No LLM API keys found. Please set GROQ_API_KEY or GEMINI_API_KEY in .env")
            
        self.groq_client = Groq(api_key=self.groq_api_key) if self.groq_api_key and Groq else None
        
        if self.gemini_api_key and genai:
            self.gemini_client = genai.Client(api_key=self.gemini_api_key)
        else:
            self.gemini_client = None

    def _format_context(self, chunks: List[Dict]) -> str:
        # Edge Case 3.B.6: Cap context to top-3 chunks to prevent context window overflow
        capped_chunks = chunks[:3]
        context_parts = []
        for c in capped_chunks:
            # Tag context explicitly with the scheme name
            scheme = c.get('metadata', {}).get('scheme_name', 'Unknown Scheme')
            text = c.get('content', '').strip()
            context_parts.append(f"[Scheme: {scheme}]\n{text}")
        return "\n\n".join(context_parts)

    def _enforce_length(self, text: str) -> str:
        # Edge Case 3.B.4: Force LLM response to be <= 3 sentences post-generation
        # Simple heuristic split on sentence boundaries
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        if len(sentences) > 3:
            return " ".join(sentences[:3])
        return text.strip()

    def generate(self, query: str, chunks: List[Dict]) -> Dict:
        if not chunks:
            return {"answer": "I don't have this information in my current data."}
            
        context_str = self._format_context(chunks)
        prompt = PROMPT_TEMPLATE.format(context=context_str, query=query)
        
        answer = None
        error_msg = None

        # Primary: Groq API
        if self.groq_client:
            try:
                logging.info("Attempting generation with Groq...")
                chat_completion = self.groq_client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    model="llama-3.1-8b-instant",
                    temperature=0.0, # Edge Case 6.B.1: Deterministic evaluation
                    max_tokens=150
                )
                answer = chat_completion.choices[0].message.content
                logging.info("Groq generation successful.")
            except Exception as e:
                logging.warning(f"Groq API failed: {e}. Falling back to secondary LLM.")
                error_msg = str(e)
        
        # Edge Case 3.B.1: Fallback to Gemini Flash
        if not answer and self.gemini_client:
            try:
                logging.info("Attempting generation with Gemini Flash...")
                response = self.gemini_client.models.generate_content(
                    model='gemini-2.5-flash',
                    contents=prompt,
                    config=genai.types.GenerateContentConfig(
                        temperature=0.0,
                        max_output_tokens=150,
                    )
                )
                answer = response.text
                logging.info("Gemini generation successful.")
            except Exception as e:
                logging.error(f"Gemini API failed: {e}")
                error_msg = str(e)

        if not answer:
            return {"error": "Failed to generate response due to API limits or errors.", "details": error_msg}

        # Edge Case 3.B.4: Enforce sentence length
        final_answer = self._enforce_length(answer)
        
        return {"answer": final_answer}

if __name__ == "__main__":
    generator = Generator()
    test_chunks = [
        {
            "content": "The expense ratio of Quant Small Cap Fund is 0.72%. The exit load is 1% if redeemed within 1 year.",
            "metadata": {"scheme_name": "Quant Small Cap Fund – Direct Plan Growth"}
        }
    ]
    res = generator.generate("What is the expense ratio?", test_chunks)
    print("Result:", res)
