import json
import random
from pathlib import Path
from typing import Dict, List
from config import NUM_EVALUATION_REPORTS, RESULTS_DIR
from src.report_generator import ReportGenerator

class EvaluationDatasetGenerator:
    def __init__(self):
        self.generator = ReportGenerator()
        self.companies = [
            "TechCorp Inc.", "DataFlow Systems", "CloudNine Solutions",
            "NeuralNetworks Ltd.", "QuantumLeap Technologies", "SoftwareFirst Corp",
            "InfoSecurity Global", "CloudCompute Inc.", "AIInnovations Ltd.",
            "DataVault Systems", "CyberShield Tech", "WebScale Networks",
            "EdgeCompute Solutions", "SmartAnalytics Inc.", "RoboticsSystems Ltd.",
            "AutomationPro Tech", "FutureTech Innovations", "DigitalTransform Corp",
            "SmartCloud Solutions", "NextGen Analytics"
        ]

        self.segments = ["Technology", "Finance", "Healthcare", "Retail", "Manufacturing"]
        self.products = {
            "Technology": ["Cloud Platform", "API Gateway", "Data Analytics", "ML Suite"],
            "Finance": ["Trading System", "Risk Analytics", "Portfolio Management", "Compliance"],
            "Healthcare": ["EHR System", "Telemedicine Platform", "Patient Analytics", "Billing"],
            "Retail": ["POS System", "Inventory Management", "Customer Analytics", "E-commerce"],
            "Manufacturing": ["Production Planning", "Quality Control", "Supply Chain", "Maintenance"]
        }

    def generate_financial_data(self, base_revenue: float = None) -> Dict:
        if base_revenue is None:
            base_revenue = random.uniform(500000, 10000000)

        growth_rate = random.uniform(5, 50)
        revenue_previous = base_revenue / (1 + growth_rate / 100)
        net_income = base_revenue * random.uniform(0.05, 0.3)
        operating_margin = (net_income / base_revenue) * 100

        segment = random.choice(self.segments)
        products = random.sample(self.products[segment], k=min(3, len(self.products[segment])))

        return {
            'revenue_current': round(base_revenue),
            'revenue_previous': round(revenue_previous),
            'net_income': round(net_income),
            'operating_margin': round(operating_margin, 1),
            'growth_rate': round(growth_rate, 1),
            'employees': random.randint(50, 5000),
            'segment': segment,
            'products': products
        }

    def generate_dataset(self, num_reports: int = NUM_EVALUATION_REPORTS) -> List[Dict]:
        dataset = []
        output_dir = RESULTS_DIR / "evaluation_dataset"
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"Generating {num_reports} evaluation reports...")

        for i in range(num_reports):
            company = random.choice(self.companies)
            financial_data = self.generate_financial_data()

            print(f"  [{i+1}/{num_reports}] Generating report for {company}...")

            result = self.generator.generate_report(company, financial_data)

            if result['success']:
                report_entry = {
                    "id": f"report_{i+1:03d}",
                    "document_id": result['document_id'],
                    "company": company,
                    "financial_data": financial_data,
                    "content": result['content'],
                    "contradictions_detected": result['contradictions_found'],
                    "contradictions": result.get('contradictions', [])
                }
                dataset.append(report_entry)

                report_file = output_dir / f"report_{i+1:03d}.json"
                with open(report_file, 'w') as f:
                    json.dump(report_entry, f, indent=2)
            else:
                print(f"    Error generating report: {result.get('error')}")

        metadata = {
            "total_reports": len(dataset),
            "total_contradictions": sum(r['contradictions_detected'] for r in dataset),
            "average_contradictions_per_report": sum(r['contradictions_detected'] for r in dataset) / len(dataset) if dataset else 0
        }

        metadata_file = output_dir / "metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        dataset_file = RESULTS_DIR / "evaluation_dataset.json"
        with open(dataset_file, 'w') as f:
            json.dump(dataset, f, indent=2)

        print(f"\nDataset generation complete!")
        print(f"  Total reports: {len(dataset)}")
        print(f"  Total contradictions: {metadata['total_contradictions']}")
        print(f"  Average contradictions per report: {metadata['average_contradictions_per_report']:.2f}")
        print(f"  Dataset saved to: {dataset_file}")

        return dataset

if __name__ == "__main__":
    generator = EvaluationDatasetGenerator()
    dataset = generator.generate_dataset()
