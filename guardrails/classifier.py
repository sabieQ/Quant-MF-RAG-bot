import re

# Edge Case 4.A.1, 4.A.2: Mixed intent and rephrased advisory
ADVISORY_KEYWORDS = [
    "should i", "invest", "recommend", "advice", "suggest", "good time to", 
    "is it safe", "worth my money", "better than", "buy", "sell", "hold",
    "put my life savings", "put my money"
]

# Edge Case 4.A.3: Factual whitelist
WHITELIST = ["risk rating", "riskometer", "risk category", "minimum investment", "sip investment"]

# Edge Case 4.C.4: Out-of-scope AMC
OUT_OF_SCOPE_AMCS = ["sbi", "hdfc", "icici", "nippon", "axis", "kotak", "tata", "uti", "dsp", "mirae"]

class QueryClassifier:
    def classify(self, query: str) -> dict:
        q = query.lower().strip()
        
        # Edge Case 4.A.5: Empty query
        if not q or q in ["?", "hi", "hello"]:
            return {"status": "empty", "message": "Hi! Please ask a specific question about Quant Mutual Fund schemes."}
            
        # Edge Case 4.A.6: Very long query (performance/injection risk)
        if len(q) > 300:
            return {"status": "too_long", "message": "Your question is too long. Please keep it under 300 characters."}
            
        # Edge Case 4.C.4: Out-of-scope AMC
        for amc in OUT_OF_SCOPE_AMCS:
            if amc in q:
                return {"status": "out_of_scope", "message": "I only have data for Quant Mutual Fund schemes."}
                
        # Remove whitelisted terms before checking advisory
        q_cleaned = q
        for wl in WHITELIST:
            q_cleaned = q_cleaned.replace(wl, "")
            
        # Edge Case 4.A.1 & 4.A.2: Mixed/Rephrased intent
        for adv in ADVISORY_KEYWORDS:
            if adv in q_cleaned:
                return {"status": "advisory", "message": None}
                
        return {"status": "informative", "message": None}
