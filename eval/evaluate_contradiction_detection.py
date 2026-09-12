"""
Comprehensive evaluation of contradiction detection system
- Recall: detection rate on 30 manually crafted contradictions
- Precision: false positive rate on 100 synthetic reports
- F1 score
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple
from tqdm import tqdm
from config import RESULTS_DIR, CONTRADICTION_THRESHOLD
from src.contradiction_detector import ContradictionDetector

def load_test_contradictions() -> List[Dict]:
    """Load 30 manually crafted contradiction pairs"""
    test_file = RESULTS_DIR / "test_contradictions_dataset.json"
    with open(test_file, 'r') as f:
        dataset = json.load(f)

    contradictions = []
    for report in dataset:
        for cont in report['contradictions']:
            contradictions.append({
                'claim_1': cont['claim_1'],
                'claim_2': cont['claim_2'],
                'company': report['company'],
                'report_id': report['id'],
                'system_score': cont['score'],
                'true_label': 1  # All test data are true contradictions
            })

    return contradictions

def load_synthetic_reports() -> List[Dict]:
    """Load 100 synthetic reports for false positive testing"""
    dataset_file = RESULTS_DIR / "evaluation_dataset.json"
    with open(dataset_file, 'r') as f:
        dataset = json.load(f)
    return dataset

def extract_claim_pairs_from_reports(reports: List[Dict], pairs_per_report: int = 2) -> List[Dict]:
    """Extract claim pairs from synthetic reports to test for false positives"""
    import random

    pairs = []
    claim_counter = 0

    for report in reports:
        # Extract sentences from report content
        sentences = [s.strip() for s in report['content'].split('.') if s.strip()]

        # Create pairs from consecutive sentences (likely non-contradictory)
        for i in range(len(sentences) - 1):
            if claim_counter >= len(reports) * pairs_per_report:
                break

            pairs.append({
                'claim_1': sentences[i],
                'claim_2': sentences[i + 1],
                'company': report['company'],
                'report_id': report['id'],
                'true_label': 0  # These should NOT be contradictions
            })
            claim_counter += 1

        if claim_counter >= len(reports) * pairs_per_report:
            break

    return pairs

def evaluate_contradiction_detection() -> Dict:
    """Run complete evaluation"""

    print("=" * 70)
    print("CONTRADICTION DETECTION EVALUATION")
    print("=" * 70)

    detector = ContradictionDetector()

    # Load test data
    print("\n[1/4] Loading test contradictions...")
    test_contradictions = load_test_contradictions()
    print(f"  ✓ Loaded {len(test_contradictions)} manually crafted contradictions")

    print("\n[2/4] Loading synthetic reports for false positive testing...")
    synthetic_reports = load_synthetic_reports()
    non_contradictions = extract_claim_pairs_from_reports(synthetic_reports, pairs_per_report=2)
    print(f"  ✓ Extracted {len(non_contradictions)} non-contradiction pairs from {len(synthetic_reports)} reports")

    # Test on manual contradictions (Recall test)
    print("\n[3/4] Testing RECALL on manual contradictions...")
    tp = 0  # True positives
    detection_results = []

    for i, pair in enumerate(tqdm(test_contradictions)):
        scores = detector.detect_contradiction(pair['claim_1'], pair['claim_2'])
        pred = 1 if scores['contradiction'] > CONTRADICTION_THRESHOLD else 0

        if pred == 1:
            tp += 1

        detection_results.append({
            'claim_1': pair['claim_1'][:60] + '...',
            'claim_2': pair['claim_2'][:60] + '...',
            'true_label': pair['true_label'],
            'predicted_label': pred,
            'contradiction_score': scores['contradiction'],
            'correct': pred == pair['true_label']
        })

    recall = tp / len(test_contradictions) if test_contradictions else 0
    print(f"\n  True Positives (detected contradictions): {tp}/{len(test_contradictions)}")
    print(f"  Recall: {recall:.4f} ({recall*100:.2f}%)")

    # Test on non-contradictions (Precision test)
    print("\n[4/4] Testing PRECISION on non-contradiction pairs...")
    tn = 0  # True negatives

    for pair in tqdm(non_contradictions):
        scores = detector.detect_contradiction(pair['claim_1'], pair['claim_2'])
        pred = 1 if scores['contradiction'] > CONTRADICTION_THRESHOLD else 0

        if pred == 0:  # Correctly identified as non-contradiction
            tn += 1

    fp = len(non_contradictions) - tn  # False positives
    precision = tn / len(non_contradictions) if non_contradictions else 0

    print(f"\n  True Negatives (correctly rejected): {tn}/{len(non_contradictions)}")
    print(f"  False Positives: {fp}/{len(non_contradictions)}")
    print(f"  Precision: {precision:.4f} ({precision*100:.2f}%)")

    # Calculate F1
    if precision + recall > 0:
        f1 = 2 * (precision * recall) / (precision + recall)
    else:
        f1 = 0.0

    print(f"\n  F1 Score: {f1:.4f}")

    # Compile results
    results = {
        'evaluation_date': str(Path(RESULTS_DIR).stat().st_mtime),
        'model': 'microsoft/deberta-v3-large',
        'threshold': CONTRADICTION_THRESHOLD,
        'recall': {
            'true_positives': tp,
            'total_contradictions': len(test_contradictions),
            'recall_score': float(recall),
            'recall_percentage': float(recall * 100)
        },
        'precision': {
            'true_negatives': tn,
            'false_positives': fp,
            'total_non_contradictions': len(non_contradictions),
            'precision_score': float(precision),
            'precision_percentage': float(precision * 100)
        },
        'f1_score': float(f1),
        'sample_detections': detection_results[:10],  # First 10 for reference
        'interpretation': {
            'recall_interpretation': f"System detected {tp} out of {len(test_contradictions)} intentional contradictions",
            'precision_interpretation': f"System had {fp} false positives out of {len(non_contradictions)} non-contradiction pairs",
            'f1_interpretation': f"Harmonic mean of precision and recall: {f1:.4f}"
        }
    }

    return results

def main():
    # Run evaluation
    results = evaluate_contradiction_detection()

    # Save results
    results_file = RESULTS_DIR / "evaluation_results.json"
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 70)
    print("EVALUATION COMPLETE")
    print("=" * 70)
    print(f"\nResults saved to: {results_file}")

    print("\n📊 FINAL METRICS:")
    print(f"  Recall:    {results['recall']['recall_percentage']:.2f}%")
    print(f"  Precision: {results['precision']['precision_percentage']:.2f}%")
    print(f"  F1 Score:  {results['f1_score']:.4f}")
    print("=" * 70)

if __name__ == "__main__":
    main()
