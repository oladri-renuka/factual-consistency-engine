"""
Generate test earnings reports with intentional contradictions
"""

import json
import uuid
from pathlib import Path
from config import RESULTS_DIR, ANNOTATIONS_DIR

def create_contradictory_report(company: str, base_revenue: float, idx: int) -> dict:
    """Create a report with intentional contradictions"""

    report_id = f"test_report_{idx:03d}"
    doc_id = str(uuid.uuid4())

    # Create contradictions
    contradictions = [
        {
            "claim_1": f"Revenue increased from ${base_revenue*0.9:,.0f} to ${base_revenue:,.0f}",
            "claim_2": f"Revenue declined 5% compared to previous year",
            "paragraph": 0,
            "score": 0.92
        },
        {
            "claim_1": f"Operating margin improved to 15%",
            "claim_2": f"Profitability decreased due to rising operational costs",
            "paragraph": 1,
            "score": 0.88
        },
        {
            "claim_1": f"We maintain strong momentum with {500} employees",
            "claim_2": f"Headcount reduction of 20% resulted in operational efficiency",
            "paragraph": 2,
            "score": 0.85
        }
    ]

    content = f"""
# {company} - Earnings Report (Test Data with Contradictions)

## Executive Summary
{company} reported strong financial performance. Revenue increased from ${base_revenue*0.9:,.0f} to ${base_revenue:,.0f}, representing impressive growth. However, revenue declined 5% compared to previous year due to market challenges.

## Financial Performance
Operating margin improved to 15%, reflecting disciplined cost management. Profitability decreased due to rising operational costs, impacting overall margins.

## Workforce
We maintain strong momentum with 500 employees across all regions. Headcount reduction of 20% resulted in operational efficiency improvements.

## Forward Guidance
Looking ahead, we expect continued growth in core markets while managing cost pressures.
"""

    report_entry = {
        "id": report_id,
        "document_id": doc_id,
        "company": company,
        "content": content,
        "contradictions_detected": len(contradictions),
        "contradictions": contradictions
    }

    return report_entry

def generate_test_dataset():
    """Generate 10 test reports with contradictions"""

    companies = [
        "TechCorp Inc.", "DataFlow Systems", "CloudNine Solutions",
        "NeuralNetworks Ltd.", "QuantumLeap Technologies", "SoftwareFirst Corp",
        "InfoSecurity Global", "CloudCompute Inc.", "AIInnovations Ltd.",
        "DataVault Systems"
    ]

    dataset = []
    for i, company in enumerate(companies):
        base_revenue = 1000000 + (i * 500000)
        report = create_contradictory_report(company, base_revenue, i + 1)
        dataset.append(report)

    # Save dataset
    test_dataset_file = RESULTS_DIR / "test_contradictions_dataset.json"
    with open(test_dataset_file, 'w') as f:
        json.dump(dataset, f, indent=2)

    print(f"✓ Generated {len(dataset)} test reports with contradictions")
    print(f"  Total contradictions: {sum(r['contradictions_detected'] for r in dataset)}")
    print(f"  Saved to: {test_dataset_file}")

    return dataset

def create_annotation_tasks(dataset):
    """Create annotation tasks from contradictory reports"""

    tasks = []
    task_id = 1

    for report in dataset:
        if report['contradictions']:
            for cont in report['contradictions']:
                task = {
                    "id": task_id,
                    "data": {
                        "content": f"Claim 1: {cont['claim_1']}\n\nClaim 2: {cont['claim_2']}",
                        "report_id": report['id'],
                        "company": report.get('company', 'Unknown'),
                        "claim_1": cont['claim_1'],
                        "claim_2": cont['claim_2'],
                        "paragraph": cont.get('paragraph', 0),
                        "system_contradiction_score": cont.get('score', 0)
                    }
                }
                tasks.append(task)
                task_id += 1

    # Save tasks
    import_file = ANNOTATIONS_DIR / "label_studio_import.json"
    with open(import_file, 'w') as f:
        json.dump(tasks, f, indent=2)

    print(f"✓ Created {len(tasks)} annotation tasks")
    print(f"  Saved to: {import_file}")
    print(f"\n✓ Ready to import to Label Studio!")

    return tasks

if __name__ == "__main__":
    print("Generating test data with intentional contradictions...\n")
    dataset = generate_test_dataset()
    print()
    tasks = create_annotation_tasks(dataset)
