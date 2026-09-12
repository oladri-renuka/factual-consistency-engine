import json
import argparse
from pathlib import Path
from .evaluation_dataset import EvaluationDatasetGenerator
from .evaluation_metrics import EvaluationMetrics
from .annotation_manager import AnnotationManager
from config import RESULTS_DIR
from tqdm import tqdm

def main():
    parser = argparse.ArgumentParser(description="Run full evaluation pipeline")
    parser.add_argument("--generate-dataset", action="store_true",
                       help="Generate 100 evaluation reports")
    parser.add_argument("--annotate", action="store_true",
                       help="Prepare annotation tasks for Label Studio")
    parser.add_argument("--evaluate", action="store_true",
                       help="Calculate evaluation metrics")
    parser.add_argument("--all", action="store_true",
                       help="Run all steps")

    args = parser.parse_args()

    if args.all or args.generate_dataset:
        print("\n" + "="*60)
        print("STEP 1: Generating Evaluation Dataset")
        print("="*60)
        generator = EvaluationDatasetGenerator()
        dataset = generator.generate_dataset()

    if args.all or args.annotate:
        print("\n" + "="*60)
        print("STEP 2: Preparing Annotation Tasks")
        print("="*60)
        prepare_annotation_tasks()

    if args.all or args.evaluate:
        print("\n" + "="*60)
        print("STEP 3: Evaluating Results")
        print("="*60)
        evaluate_results()

def prepare_annotation_tasks():
    dataset_file = RESULTS_DIR / "evaluation_dataset.json"

    if not dataset_file.exists():
        print("Error: evaluation_dataset.json not found. Run with --generate-dataset first.")
        return

    with open(dataset_file, 'r') as f:
        dataset = json.load(f)

    ann_manager = AnnotationManager()

    print(f"Preparing {len(dataset)} annotation tasks for Label Studio...")

    annotation_tasks = []
    for report in tqdm(dataset, desc="Creating tasks"):
        task_id = ann_manager.create_annotation_task(
            report['id'],
            report['document_id']
        )

        if report['contradictions']:
            for cont in report['contradictions']:
                annotation_tasks.append({
                    "task_id": task_id,
                    "report_id": report['id'],
                    "claim_1": cont['claim_1'],
                    "claim_2": cont['claim_2'],
                    "paragraph": cont.get('paragraph', 0),
                    "system_detected": True
                })

    tasks_file = RESULTS_DIR / "annotation_tasks.json"
    with open(tasks_file, 'w') as f:
        json.dump(annotation_tasks, f, indent=2)

    ann_manager.close()

    print(f"✓ Created {len(annotation_tasks)} annotation tasks")
    print(f"  Saved to: {tasks_file}")
    print(f"  Ready for import to Label Studio")

def evaluate_results():
    metrics = EvaluationMetrics()

    dataset_file = RESULTS_DIR / "evaluation_dataset.json"
    if not dataset_file.exists():
        print("Error: evaluation_dataset.json not found")
        return

    with open(dataset_file, 'r') as f:
        dataset = json.load(f)

    print(f"Evaluating {len(dataset)} reports...")

    overall_report = metrics.generate_evaluation_report(dataset)

    results = {
        "evaluation_timestamp": str(Path(RESULTS_DIR).stat().st_mtime),
        "dataset_statistics": overall_report,
        "model_performance": {
            "contradiction_detection": {
                "note": "Calculate after human annotation ground truth available",
                "metrics": {
                    "precision": "TBD",
                    "recall": "TBD",
                    "f1": "TBD"
                }
            }
        },
        "inter_annotator_agreement": {
            "note": "Calculate after annotations from 2+ annotators",
            "cohens_kappa": "TBD",
            "agreement_rate": "TBD"
        }
    }

    results_file = metrics.save_evaluation_results(results)
    print(f"✓ Evaluation report saved to: {results_file}")

    print("\n" + "="*60)
    print("EVALUATION SUMMARY")
    print("="*60)
    print(f"Total Reports: {overall_report['total_reports']}")
    print(f"Total Contradictions Detected: {overall_report['total_contradictions_detected']}")
    print(f"Avg Contradictions/Report: {overall_report['average_contradictions_per_report']:.2f}")
    print(f"Reports with Contradictions: {overall_report['reports_with_contradictions']}")
    print(f"\nContradiction Distribution:")
    for count, freq in overall_report['contradiction_distribution'].items():
        print(f"  {count} contradictions: {freq} reports")

    metrics.close()

if __name__ == "__main__":
    main()
