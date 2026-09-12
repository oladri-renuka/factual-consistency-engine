import requests
import json
from typing import List, Dict, Optional, Tuple
import re
import uuid
from config import (
    OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL,
    MAX_TOKENS, TEMPERATURE, CONTRADICTION_THRESHOLD
)
from .fact_ledger import FactLedger
from .claim_extractor import ClaimExtractor
from .embeddings import EmbeddingService
from .contradiction_detector import ContradictionDetector
import numpy as np

class ReportGenerator:
    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self.base_url = OPENROUTER_BASE_URL
        self.model = OPENROUTER_MODEL
        self.ledger = FactLedger()
        self.claim_extractor = ClaimExtractor()
        self.embeddings = EmbeddingService()
        self.contradiction_detector = ContradictionDetector()

    def generate_report(self, company: str, financial_data: Dict,
                       check_contradictions: bool = True) -> Dict:
        doc_id = str(uuid.uuid4())
        self.ledger.add_document(doc_id, f"Earnings Report: {company}")

        prompt = self._build_prompt(company, financial_data)

        full_text = ""
        paragraph_num = 0
        caught_contradictions = []

        messages = [{"role": "user", "content": prompt}]

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": messages,
                    "max_tokens": MAX_TOKENS,
                    "temperature": TEMPERATURE,
                    "stream": False
                },
                timeout=60
            )

            if response.status_code != 200:
                return {
                    "success": False,
                    "error": f"API error: {response.status_code}",
                    "status_code": response.status_code
                }

            result = response.json()
            full_text = result["choices"][0]["message"]["content"]

            if check_contradictions:
                paragraphs = [p.strip() for p in full_text.split("\n\n") if p.strip()]

                for para_num, paragraph in enumerate(paragraphs):
                    claims = self.claim_extractor.extract_claims(paragraph)

                    for claim_text, confidence in claims:
                        embedding = self.embeddings.encode(claim_text)

                        existing_claims = self.ledger.get_claims_by_document(doc_id)

                        for existing_claim in existing_claims:
                            if existing_claim.embedding is not None:
                                similarity = self.embeddings.similarity(
                                    embedding,
                                    existing_claim.embedding
                                )

                                if similarity > 0.75:
                                    scores = self.contradiction_detector.detect_contradiction(
                                        existing_claim.text,
                                        claim_text
                                    )

                                    if scores["contradiction"] > CONTRADICTION_THRESHOLD:
                                        caught_contradictions.append({
                                            "claim_1": existing_claim.text,
                                            "claim_2": claim_text,
                                            "score": scores["contradiction"],
                                            "paragraph": para_num
                                        })

                        self.ledger.add_claim(
                            doc_id, claim_text, embedding,
                            para_num, confidence
                        )

            return {
                "success": True,
                "document_id": doc_id,
                "content": full_text,
                "contradictions_found": len(caught_contradictions),
                "contradictions": caught_contradictions
            }

        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"Request failed: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error: {str(e)}"
            }

    def _build_prompt(self, company: str, financial_data: Dict) -> str:
        prompt = f"""
Generate a comprehensive earnings report for {company} based on the following financial data:

Revenue (Current): ${financial_data.get('revenue_current', 1000000):,}
Revenue (Previous Year): ${financial_data.get('revenue_previous', 900000):,}
Net Income: ${financial_data.get('net_income', 150000):,}
Operating Margin: {financial_data.get('operating_margin', 15)}%
Growth Rate: {financial_data.get('growth_rate', 11.1)}%
Employees: {financial_data.get('employees', 500)}
Market Segment: {financial_data.get('segment', 'Technology')}
Key Products: {', '.join(financial_data.get('products', ['Product A', 'Product B']))}

Please write a detailed 3-4 paragraph earnings report that includes:
1. Executive Summary with key metrics
2. Revenue and profitability analysis
3. Business segment performance
4. Forward-looking guidance

Ensure the report is professional and maintains internal consistency.
"""
        return prompt.strip()

    def close(self):
        self.ledger.close()
