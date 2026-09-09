import gradio as gr
from report_generator import ReportGenerator
from typing import Dict, Tuple
import json

class EarningsReportInterface:
    def __init__(self):
        self.generator = ReportGenerator()

    def generate_with_company_info(self, company_name: str, revenue: str,
                                   growth_rate: str, employees: str) -> Tuple[str, str, str]:
        try:
            financial_data = {
                'revenue_current': float(revenue) if revenue else 1000000,
                'revenue_previous': float(revenue) * 0.9 if revenue else 900000,
                'net_income': float(revenue) * 0.15 if revenue else 150000,
                'operating_margin': 15,
                'growth_rate': float(growth_rate) if growth_rate else 11.1,
                'employees': int(employees) if employees else 500,
                'segment': 'Technology',
                'products': ['Core Platform', 'Enterprise Suite', 'Analytics Tools']
            }

            result = self.generator.generate_report(company_name, financial_data)

            if not result['success']:
                return f"Error: {result.get('error', 'Unknown error')}", "", ""

            content = result['content']
            contradictions = result.get('contradictions', [])

            baseline_with_highlights = self._highlight_contradictions(content, contradictions)

            contradictions_text = f"Contradictions Found: {result['contradictions_found']}\n\n"
            if contradictions:
                for i, cont in enumerate(contradictions, 1):
                    contradictions_text += f"{i}. Claim 1: {cont['claim_1']}\n"
                    contradictions_text += f"   Claim 2: {cont['claim_2']}\n"
                    contradictions_text += f"   Score: {cont['score']:.2f}\n"
                    contradictions_text += f"   Paragraph: {cont['paragraph']}\n\n"

            return content, baseline_with_highlights, contradictions_text

        except Exception as e:
            return f"Error: {str(e)}", "", ""

    def _highlight_contradictions(self, text: str, contradictions: list) -> str:
        html_output = "<div style='font-family: Arial; line-height: 1.6;'>"
        html_output += "<h3>Baseline Report (with contradictions highlighted)</h3>"
        html_output += "<p style='background-color: #fff3cd; padding: 10px; margin-bottom: 20px;'>"
        html_output += "⚠️ Red highlights indicate detected contradictions that need resolution."
        html_output += "</p>"

        lines = text.split('\n')
        for line in lines:
            highlighted_line = line
            for cont in contradictions:
                if cont['claim_1'].lower() in line.lower():
                    highlighted_line = highlighted_line.replace(
                        line,
                        f"<mark style='background-color: #ffcccc; color: red;'>{line}</mark>"
                    )

            html_output += f"<p>{highlighted_line}</p>"

        html_output += "</div>"
        return html_output

    def launch(self):
        with gr.Blocks(title="Financial Earnings Report Generator") as demo:
            gr.Markdown("# Financial Earnings Report Generator")
            gr.Markdown("Generate earnings reports with real-time contradiction detection and fixing")

            with gr.Row():
                company_name = gr.Textbox(
                    label="Company Name",
                    placeholder="e.g., TechCorp Inc.",
                    value="TechCorp Inc."
                )

            with gr.Row():
                with gr.Column():
                    revenue = gr.Number(
                        label="Current Revenue ($)",
                        value=1000000,
                        step=100000
                    )
                with gr.Column():
                    growth_rate = gr.Number(
                        label="Growth Rate (%)",
                        value=11.1,
                        step=0.1
                    )
                with gr.Column():
                    employees = gr.Number(
                        label="Number of Employees",
                        value=500,
                        step=10
                    )

            generate_btn = gr.Button("Generate Report", variant="primary", size="lg")

            gr.Markdown("---")
            gr.Markdown("## Report Comparison")

            with gr.Row():
                with gr.Column(label="Generated Report"):
                    generated_output = gr.Textbox(
                        label="Clean Report (Contradictions Fixed)",
                        lines=15,
                        interactive=False
                    )

                with gr.Column(label="Baseline Comparison"):
                    baseline_output = gr.HTML(
                        label="Baseline Report (Contradictions Highlighted)"
                    )

            contradictions_output = gr.Textbox(
                label="Detected Contradictions",
                lines=10,
                interactive=False
            )

            generate_btn.click(
                self.generate_with_company_info,
                inputs=[company_name, revenue, growth_rate, employees],
                outputs=[generated_output, baseline_output, contradictions_output]
            )

        demo.launch(server_name="0.0.0.0", server_port=7860, share=False)


if __name__ == "__main__":
    interface = EarningsReportInterface()
    interface.launch()
