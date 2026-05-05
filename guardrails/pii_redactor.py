import re

class PIIRedactor:
    def __init__(self):
        # Edge Case 4.B.1 to 4.B.5
        self.patterns = {
            "PAN": r'\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b',
            "Aadhaar": r'\b\d{4}\s?\d{4}\s?\d{4}\b',
            "Email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "Phone": r'\b(?:\+?91[\-\s]?)?[6789]\d{9}\b'
        }

    def contains_pii(self, text: str) -> bool:
        t = text.upper()
        for name, pattern in self.patterns.items():
            if re.search(pattern, t, re.IGNORECASE):
                return True
        return False
