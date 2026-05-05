import logging
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from rag.retriever import Retriever
from rag.generator import Generator
from rag.formatter import Formatter
from guardrails.classifier import QueryClassifier
from guardrails.pii_redactor import PIIRedactor
from guardrails.refusal import RefusalHandler
from guardrails.validator import ResponseValidator

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class RAGEngine:
    def __init__(self):
        self.retriever = Retriever()
        self.generator = Generator()
        self.formatter = Formatter()
        
        # Phase 4 components
        self.classifier = QueryClassifier()
        self.pii_redactor = PIIRedactor()
        self.refusal_handler = RefusalHandler()
        self.validator = ResponseValidator()

    def query(self, user_question: str) -> str:
        logging.info(f"Processing query: {user_question}")
        
        # Guardrail 4.B: PII Filter
        if self.pii_redactor.contains_pii(user_question):
            logging.warning("PII detected in query.")
            return "For your security, I cannot process queries containing personal information (like PAN, Aadhaar, Phone, or Email)."
            
        # Guardrail 4.A: Pre-Processing Classifier
        classification = self.classifier.classify(user_question)
        if classification["status"] != "informative":
            if classification["message"]:
                return classification["message"]
            # Guardrail 4.C: Refusal Handler
            return self.refusal_handler.get_refusal(user_question)
        
        # 1. Retrieve (Phase 3.A)
        retrieval_result = self.retriever.retrieve(user_question)
        if "error" in retrieval_result:
            return retrieval_result["error"]
            
        chunks = retrieval_result["chunks"]
        
        # 2. Generate (Phase 3.B)
        gen_result = self.generator.generate(user_question, chunks)
        if "error" in gen_result:
            return f"Error: {gen_result['error']}\nDetails: {gen_result.get('details')}"
            
        llm_response = gen_result["answer"]
        
        # 3. Format with citation (Phase 3.C)
        final_output = self.formatter.format_response(llm_response, chunks)
        
        # Guardrail 4.D: Response Validator
        if not self.validator.validate(llm_response):
            logging.warning("Advisory language detected in LLM output. Rejecting.")
            return self.refusal_handler.get_refusal()
        
        return final_output

if __name__ == "__main__":
    engine = RAGEngine()
    test_queries = [
        "What is the exit load for Quant Small Cap Fund?",
        "Who is the fund manager for ELSS?",
        "How do I buy stocks?" # Should trigger out-of-context fallback
    ]
    
    for q in test_queries:
        print(f"\n--- Query: {q} ---")
        print(engine.query(q))
