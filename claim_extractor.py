import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from typing import List, Tuple
import re
import numpy as np
from config import CLAIM_EXTRACTOR_MODEL

class ClaimExtractor:
    def __init__(self, model_name: str = CLAIM_EXTRACTOR_MODEL):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()

    def extract_sentences(self, text: str) -> List[str]:
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        return [s.strip() for s in sentences if s.strip()]

    def score_claim(self, text: str) -> float:
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True,
                               max_length=512)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1)[0]

        claim_prob = float(probs[1])
        return claim_prob

    def extract_claims(self, text: str, threshold: float = 0.5) -> List[Tuple[str, float]]:
        sentences = self.extract_sentences(text)
        claims = []

        for sentence in sentences:
            if len(sentence.split()) < 3:
                continue

            confidence = self.score_claim(sentence)

            if confidence >= threshold:
                claims.append((sentence, confidence))

        return claims

    def extract_claims_batch(self, texts: List[str],
                           threshold: float = 0.5) -> List[List[Tuple[str, float]]]:
        all_claims = []
        for text in texts:
            all_claims.append(self.extract_claims(text, threshold))
        return all_claims
