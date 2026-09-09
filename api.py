from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from report_generator import ReportGenerator
from fact_ledger import FactLedger
import uvicorn

app = FastAPI(title="Factual Consistency Engine API")

class FinancialData(BaseModel):
    company_name: str
    revenue_current: float
    revenue_previous: float = None
    net_income: float
    operating_margin: float = 15
    growth_rate: float
    employees: int
    segment: str = "Technology"
    products: List[str] = ["Product A", "Product B"]

class GenerationRequest(BaseModel):
    company_name: str
    financial_data: FinancialData
    check_contradictions: bool = True

class ReportResponse(BaseModel):
    success: bool
    document_id: Optional[str] = None
    content: Optional[str] = None
    contradictions_found: int = 0
    contradictions: List[Dict] = []
    error: Optional[str] = None

generator = ReportGenerator()

@app.post("/generate", response_model=ReportResponse)
async def generate_report(request: GenerationRequest) -> ReportResponse:
    try:
        financial_data = request.financial_data.dict()
        result = generator.generate_report(
            request.company_name,
            financial_data,
            request.check_contradictions
        )

        if not result['success']:
            raise HTTPException(status_code=400, detail=result.get('error'))

        return ReportResponse(
            success=True,
            document_id=result['document_id'],
            content=result['content'],
            contradictions_found=result['contradictions_found'],
            contradictions=result.get('contradictions', [])
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/document/{document_id}")
async def get_document_claims(document_id: str):
    try:
        ledger = FactLedger()
        claims = ledger.get_claims_by_document(document_id)
        contradictions = ledger.get_contradictions_by_document(document_id)
        ledger.close()

        return {
            "document_id": document_id,
            "claims": [
                {
                    "id": c.id,
                    "text": c.text,
                    "paragraph": c.paragraph_number,
                    "confidence": c.confidence
                }
                for c in claims
            ],
            "contradictions": contradictions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "Factual Consistency Engine"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
