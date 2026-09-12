import numpy as np
from typing import List, Dict, Tuple
from scipy.stats import contingency
from sklearn.metrics import cohen_kappa_score, precision_score, recall_score, f1_score
from pathlib import Path
import json
from config import RESULTS_DIR
from .annotation_manager import AnnotationManager

class EvaluationMetrics:
    def __init__(self):
        self.ann_manager = AnnotationManager()

    def calculate_cohens_kappa(self, annotator_1_labels: List[int],
                              annotator_2_labels: List[int]) -> float:
        if len(annotator_1_labels) != len(annotator_2_labels):
            raise ValueError("Annotator label lists must have same length")

        if len(annotator_1_labels) == 0:
            return 0.0

        return float(cohen_kappa_score(annotator_1_labels, annotator_2_labels))

    def calculate_inter_annotator_agreement(self, report_id: str,
                                           annotator_1: str,
                                           annotator_2: str) -> Dict:
        agreement_data = self.ann_manager.get_annotator_pair_annotations(
            report_id, annotator_1, annotator_2
        )

        if agreement_data['common_annotations'] == 0:
            return {
                'report_id': report_id,
                'annotator_1': annotator_1,
                'annotator_2': annotator_2,
                'cohens_kappa': 0.0,
                'agreement_rate': 0.0,
                'common_annotations': 0
            }

        labels_1 = []
        labels_2 = []

        annotations_1 = self.ann_manager.get_annotations_by_report(report_id)
        annotations_2 = self.ann_manager.get_annotations_by_report(report_id)

        ann_dict_1 = {(a['claim_1'], a['claim_2']): a['is_contradiction']
                     for a in annotations_1 if a['annotator_id'] == annotator_1}
        ann_dict_2 = {(a['claim_1'], a['claim_2']): a['is_contradiction']
                     for a in annotations_2 if a['annotator_id'] == annotator_2}

        for key in ann_dict_1:
            if key in ann_dict_2:
                labels_1.append(int(ann_dict_1[key]))
                labels_2.append(int(ann_dict_2[key]))

        if len(labels_1) == 0:
            kappa = 0.0
        else:
            kappa = self.calculate_cohens_kappa(labels_1, labels_2)

        agreement_rate = agreement_data['agree'] / agreement_data['common_annotations'] \
                        if agreement_data['common_annotations'] > 0 else 0.0

        result = {
            'report_id': report_id,
            'annotator_1': annotator_1,
            'annotator_2': annotator_2,
            'cohens_kappa': kappa,
            'agreement_rate': agreement_rate,
            'common_annotations': agreement_data['common_annotations'],
            'agreed': agreement_data['agree'],
            'disagreed': agreement_data['disagree']
        }

        self.ann_manager.save_agreement_score(
            report_id, annotator_1, annotator_2,
            agreement_data['agree'],
            agreement_data['common_annotations'],
            kappa
        )

        return result

    def calculate_contradiction_detection_metrics(self, ground_truth: List[int],
                                                 predictions: List[int]) -> Dict:
        if len(ground_truth) != len(predictions):
            raise ValueError("Ground truth and predictions must have same length")

        precision = precision_score(ground_truth, predictions, zero_division=0)
        recall = recall_score(ground_truth, predictions, zero_division=0)
        f1 = f1_score(ground_truth, predictions, zero_division=0)

        tp = sum(1 for gt, pred in zip(ground_truth, predictions)
                if gt == 1 and pred == 1)
        fp = sum(1 for gt, pred in zip(ground_truth, predictions)
                if gt == 0 and pred == 1)
        fn = sum(1 for gt, pred in zip(ground_truth, predictions)
                if gt == 1 and pred == 0)
        tn = sum(1 for gt, pred in zip(ground_truth, predictions)
                if gt == 0 and pred == 0)

        return {
            'precision': float(precision),
            'recall': float(recall),
            'f1': float(f1),
            'true_positives': tp,
            'false_positives': fp,
            'false_negatives': fn,
            'true_negatives': tn,
            'accuracy': float((tp + tn) / (tp + tn + fp + fn)) if (tp + tn + fp + fn) > 0 else 0
        }

    def generate_evaluation_report(self, dataset: List[Dict]) -> Dict:
        report = {
            'total_reports': len(dataset),
            'total_contradictions_detected': sum(r['contradictions_detected'] for r in dataset),
            'average_contradictions_per_report': sum(r['contradictions_detected'] for r in dataset) / len(dataset) if dataset else 0,
            'reports_with_contradictions': sum(1 for r in dataset if r['contradictions_detected'] > 0),
            'contradiction_distribution': self._get_contradiction_distribution(dataset)
        }

        return report

    def _get_contradiction_distribution(self, dataset: List[Dict]) -> Dict:
        distribution = {}
        for report in dataset:
            count = report['contradictions_detected']
            distribution[count] = distribution.get(count, 0) + 1

        return dict(sorted(distribution.items()))

    def save_evaluation_results(self, results: Dict, filename: str = "evaluation_results.json"):
        output_path = RESULTS_DIR / filename
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        return output_path

    def close(self):
        self.ann_manager.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
