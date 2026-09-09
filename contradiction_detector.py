import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from typing import List, Dict, Tuple
import numpy as np
from config import NLI_MODEL, CONTRADICTION_THRESHOLD

class ContradictionDetector:
    def __init__(self, model_name: str = NLI_MODEL):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()
        self.label2id = {"contradiction": 0, "neutral": 1, "entailment": 2}
        self.id2label = {v: k for k, v in self.label2id.items()}

    def detect_contradiction(self, premise: str, hypothesis: str) -> Dict[str, float]:
        inputs = self.tokenizer(premise, hypothesis, return_tensors="pt",
                               truncation=True, max_length=512)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=-1)[0]

        scores = {
            "contradiction": float(probs[0]),
            "neutral": float(probs[1]),
            "entailment": float(probs[2])
        }

        return scores

    def batch_detect_contradictions(self, premises: List[str],
                                   hypotheses: List[str]) -> List[Dict[str, float]]:
        results = []
        for premise, hypothesis in zip(premises, hypotheses):
            results.append(self.detect_contradiction(premise, hypothesis))
        return results

    def find_contradictions(self, claims: List[str]) -> List[Tuple[int, int, float]]:
        contradictions = []

        for i in range(len(claims)):
            for j in range(i + 1, len(claims)):
                scores_ij = self.detect_contradiction(claims[i], claims[j])
                scores_ji = self.detect_contradiction(claims[j], claims[i])

                contradiction_prob = max(scores_ij["contradiction"],
                                        scores_ji["contradiction"])

                if contradiction_prob > CONTRADICTION_THRESHOLD:
                    contradictions.append((i, j, contradiction_prob))

        return contradictions

    def is_contradictory(self, premise: str, hypothesis: str,
                        threshold: float = CONTRADICTION_THRESHOLD) -> bool:
        scores = self.detect_contradiction(premise, hypothesis)
        return scores["contradiction"] > threshold
