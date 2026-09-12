#!/usr/bin/env python3
"""
Demo script showing the complete factual consistency engine workflow
"""

import json
from pathlib import Path
from src.report_generator import ReportGenerator
from src.fact_ledger import FactLedger
from src.embeddings import EmbeddingService
from src.contradiction_detector import ContradictionDetector
from src.claim_extractor import ClaimExtractor

def demo_single_report():
    print("\n" + "="*70)
    print("DEMO: Single Report Generation with Contradiction Detection")
    print("="*70)

    generator = ReportGenerator()

    company = "TechCorp Inc."
    financial_data = {
        'revenue_current': 1000000,
        'revenue_previous': 900000,
        'net_income': 150000,
        'operating_margin': 15,
        'growth_rate': 11.1,
        'employees': 500,
        'segment': 'Technology',
        'products': ['Cloud Platform', 'API Gateway', 'Analytics']
    }

    print(f"\nCompany: {company}")
    print(f"Revenue: ${financial_data['revenue_current']:,}")
    print(f"Growth Rate: {financial_data['growth_rate']}%")
    print(f"Employees: {financial_data['employees']}")

    print("\n[Generating report with contradiction detection...]")
    result = generator.generate_report(company, financial_data, check_contradictions=True)

    if result['success']:
        print(f"\n✓ Report generated successfully (ID: {result['document_id'][:8]}...)")
        print(f"\nContent Preview (first 500 chars):")
        print("-" * 70)
        print(result['content'][:500] + "...\n")

        print(f"Contradictions Found: {result['contradictions_found']}")
        if result['contradictions']:
            print("\nDetected Contradictions:")
            for i, cont in enumerate(result['contradictions'], 1):
                print(f"\n  {i}. Claim 1: {cont['claim_1'][:60]}...")
                print(f"     Claim 2: {cont['claim_2'][:60]}...")
                print(f"     Score: {cont['score']:.3f}")
                print(f"     Paragraph: {cont['paragraph']}")

        ledger = FactLedger()
        claims = ledger.get_claims_by_document(result['document_id'])
        print(f"\n✓ Total claims extracted and stored: {len(claims)}")
        ledger.close()

    else:
        print(f"✗ Error: {result['error']}")

    generator.close()


def demo_components():
    print("\n" + "="*70)
    print("DEMO: Individual Component Testing")
    print("="*70)

    text = """
    TechCorp Inc. generated $1M in revenue this quarter, representing a 10%
    increase from last year. Our operating margin improved to 15%, delivering
    strong profitability. However, revenue actually declined 5% compared to Q3.
    """

    print(f"\nInput Text:\n{text}")

    print("\n" + "-"*70)
    print("1. CLAIM EXTRACTION")
    print("-"*70)
    extractor = ClaimExtractor()
    claims = extractor.extract_claims(text)
    print(f"Extracted {len(claims)} claims:")
    for claim_text, confidence in claims:
        print(f"  • {claim_text}")
        print(f"    Confidence: {confidence:.3f}")

    print("\n" + "-"*70)
    print("2. EMBEDDINGS & SIMILARITY")
    print("-"*70)
    embeddings_service = EmbeddingService()
    claim_texts = [c[0] for c in claims]
    embeddings = [embeddings_service.encode(c) for c in claim_texts]

    if len(embeddings) >= 2:
        similarity = embeddings_service.similarity(embeddings[0], embeddings[1])
        print(f"Similarity between first two claims: {similarity:.3f}")

    print("\n" + "-"*70)
    print("3. CONTRADICTION DETECTION (NLI)")
    print("-"*70)
    detector = ContradictionDetector()

    claim_pairs = [
        ("Revenue increased 10%", "Revenue declined 5%"),
        ("Operating margin is 15%", "Profitability improved"),
        ("TechCorp generated $1M", "Revenue was $1 million")
    ]

    for premise, hypothesis in claim_pairs:
        scores = detector.detect_contradiction(premise, hypothesis)
        print(f"\nPremise: {premise}")
        print(f"Hypothesis: {hypothesis}")
        print(f"  Contradiction: {scores['contradiction']:.3f}")
        print(f"  Entailment: {scores['entailment']:.3f}")
        print(f"  Neutral: {scores['neutral']:.3f}")

        contradiction_status = "CONTRADICTION" if scores['contradiction'] > 0.7 else "OK"
        print(f"  Status: {contradiction_status}")


def demo_fact_ledger():
    print("\n" + "="*70)
    print("DEMO: Fact Ledger Database Operations")
    print("="*70)

    import numpy as np
    import uuid

    ledger = FactLedger()
    doc_id = str(uuid.uuid4())[:8]

    print(f"\nDocument ID: {doc_id}")
    print("\n[Adding document to ledger...]")
    ledger.add_document(doc_id, "Test Report")

    print("[Adding claims with embeddings...]")
    embeddings_service = EmbeddingService()

    test_claims = [
        ("Revenue increased 10% YoY", 0.95),
        ("Net income reached $150K", 0.92),
        ("Operating margin is 15%", 0.88)
    ]

    claim_ids = []
    for claim_text, confidence in test_claims:
        embedding = embeddings_service.encode(claim_text)
        claim_id = ledger.add_claim(
            doc_id, claim_text, embedding, 0, confidence
        )
        claim_ids.append(claim_id)
        print(f"  • Stored: {claim_text[:50]}... (ID: {claim_id})")

    print("\n[Retrieving claims from ledger...]")
    retrieved_claims = ledger.get_claims_by_document(doc_id)
    print(f"Retrieved {len(retrieved_claims)} claims:")
    for claim in retrieved_claims:
        print(f"  • {claim.text[:50]}...")
        print(f"    Confidence: {claim.confidence:.2f}")

    if len(claim_ids) >= 2:
        print(f"\n[Storing contradiction between claims...]")
        ledger.add_contradiction(doc_id, claim_ids[0], claim_ids[1], 0.85)

        contradictions = ledger.get_contradictions_by_document(doc_id)
        print(f"Retrieved {len(contradictions)} contradiction(s):")
        for cont in contradictions:
            print(f"  • Score: {cont['score']:.3f}")
            print(f"    Claim 1: {cont['claim_1'][:50]}...")
            print(f"    Claim 2: {cont['claim_2'][:50]}...")

    ledger.close()
    print("\n✓ Database operations complete")


def main():
    print("\n" + "="*70)
    print("FACTUAL CONSISTENCY ENGINE - DEMO")
    print("="*70)

    print("\nThis demo showcases the main components of the system:")
    print("  1. Report generation with contradiction detection")
    print("  2. Individual component testing (extraction, embeddings, NLI)")
    print("  3. Fact ledger database operations")

    try:
        demo_single_report()
    except Exception as e:
        print(f"\n✗ Error in report generation: {e}")
        print("  Make sure OPENROUTER_API_KEY is set")

    try:
        demo_components()
    except Exception as e:
        print(f"\n✗ Error in component demo: {e}")

    try:
        demo_fact_ledger()
    except Exception as e:
        print(f"\n✗ Error in ledger demo: {e}")

    print("\n" + "="*70)
    print("Demo Complete!")
    print("="*70)
    print("\nNext Steps:")
    print("  1. Run Gradio interface: python gradio_interface.py")
    print("  2. Start API server: python api.py")
    print("  3. Generate evaluation dataset: python evaluation_dataset.py")
    print("  4. Run full evaluation: python run_evaluation.py --all")


if __name__ == "__main__":
    main()
