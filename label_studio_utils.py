import json
import csv
from pathlib import Path
from typing import List, Dict
from config import RESULTS_DIR, ANNOTATIONS_DIR
from annotation_manager import AnnotationManager

class LabelStudioExporter:
    def __init__(self):
        self.ann_manager = AnnotationManager()

    def export_to_label_studio_json(self, reports: List[Dict],
                                   output_file: str = None) -> str:
        if output_file is None:
            output_file = ANNOTATIONS_DIR / "label_studio_import.json"

        tasks = []
        task_id = 1

        for report in reports:
            if report.get('contradictions'):
                for cont in report['contradictions']:
                    task = {
                        "id": task_id,
                        "data": {
                            "report_id": report['id'],
                            "company": report.get('company', 'Unknown'),
                            "claim_1": cont['claim_1'],
                            "claim_2": cont['claim_2'],
                            "paragraph": cont.get('paragraph', 0),
                            "system_contradiction_score": cont.get('score', 0),
                            "text": f"Claim 1: {cont['claim_1']}\n\nClaim 2: {cont['claim_2']}"
                        }
                    }
                    tasks.append(task)
                    task_id += 1

        with open(output_file, 'w') as f:
            json.dump(tasks, f, indent=2)

        return str(output_file)

    def export_to_csv(self, reports: List[Dict],
                     output_file: str = None) -> str:
        if output_file is None:
            output_file = ANNOTATIONS_DIR / "annotation_tasks.csv"

        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                'task_id', 'report_id', 'company', 'claim_1', 'claim_2',
                'paragraph', 'system_score'
            ])

            task_id = 1
            for report in reports:
                if report.get('contradictions'):
                    for cont in report['contradictions']:
                        writer.writerow([
                            task_id,
                            report['id'],
                            report.get('company', 'Unknown'),
                            cont['claim_1'],
                            cont['claim_2'],
                            cont.get('paragraph', 0),
                            f"{cont.get('score', 0):.3f}"
                        ])
                        task_id += 1

        return str(output_file)

    def import_label_studio_export(self, export_file: str,
                                  annotator_id: str) -> Dict:
        with open(export_file, 'r') as f:
            export_data = json.load(f)

        results = {
            'total_tasks': 0,
            'imported': 0,
            'errors': []
        }

        for item in export_data:
            results['total_tasks'] += 1
            try:
                annotations = item.get('annotations', [])
                if not annotations:
                    results['errors'].append(f"Task {item['id']}: No annotations")
                    continue

                annotation = annotations[0]
                task_data = item['data']

                report_id = task_data.get('report_id')
                claim_1 = task_data.get('claim_1')
                claim_2 = task_data.get('claim_2')

                result = annotation['result'][0]
                is_contradiction = result['value']['choices'][0] == 'contradiction'
                notes = result.get('notes', '')

                task_id = self.ann_manager.create_annotation_task(
                    report_id,
                    report_id
                )

                self.ann_manager.add_annotation(
                    task_id=task_id,
                    annotator_id=annotator_id,
                    report_id=report_id,
                    contradiction_id=item['id'],
                    claim_1=claim_1,
                    claim_2=claim_2,
                    is_contradiction=is_contradiction,
                    confidence=1.0,
                    notes=notes
                )

                results['imported'] += 1

            except Exception as e:
                results['errors'].append(f"Task {item.get('id')}: {str(e)}")

        return results

    def close(self):
        self.ann_manager.close()


def prepare_annotation_export(dataset_file: str = None):
    if dataset_file is None:
        dataset_file = RESULTS_DIR / "evaluation_dataset.json"

    with open(dataset_file, 'r') as f:
        dataset = json.load(f)

    exporter = LabelStudioExporter()

    json_file = exporter.export_to_label_studio_json(dataset)
    csv_file = exporter.export_to_csv(dataset)

    exporter.close()

    return {
        'json_export': json_file,
        'csv_export': csv_file,
        'total_tasks': sum(len(r.get('contradictions', [])) for r in dataset)
    }


if __name__ == "__main__":
    result = prepare_annotation_export()
    print("Label Studio Export Complete!")
    print(f"JSON Export: {result['json_export']}")
    print(f"CSV Export: {result['csv_export']}")
    print(f"Total Tasks: {result['total_tasks']}")
