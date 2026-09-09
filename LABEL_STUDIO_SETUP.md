# Label Studio Setup Guide

## Overview
This guide explains how to set up Label Studio for human annotation of contradictions detected in the earnings reports.

## Installation

### Docker (Recommended)
```bash
docker run -it -p 8080:8080 heartexlabs/label-studio:latest
```

### Local Installation
```bash
pip install label-studio
label-studio start
```

Access at: http://localhost:8080

## Project Configuration

### 1. Create New Project
1. Login to Label Studio
2. Click "Create Project"
3. Name: "Earnings Report Contradiction Annotation"
4. Description: "Annotating detected contradictions in financial earnings reports"

### 2. Label Configuration

Set the following label template in `Labeling Interface > Code`:

```xml
<View>
  <Text name="text" value="$content"/>
  <Choices name="contradiction" toName="text" required="true">
    <Choice value="contradiction" background="red"/>
    <Choice value="not_contradiction" background="green"/>
    <Choice value="unsure" background="yellow"/>
  </Choices>
  <Textarea name="notes" placeholder="Add any notes or reasoning..." required="false"/>
</View>
```

### 3. Data Import

#### Option A: Import JSON Tasks
```bash
python prepare_annotation_tasks.py
```

This generates `annotation_tasks.json` which can be imported to Label Studio via:
1. Project Settings → Import
2. Select "JSON" format
3. Upload the JSON file

#### Option B: Manual CSV Import
Generate CSV:
```bash
python export_annotation_csv.py
```

### Task Format

Each annotation task should contain:
```json
{
  "id": "task_001",
  "data": {
    "report_id": "report_001",
    "claim_1": "Revenue increased 11.1% YoY",
    "claim_2": "Revenue growth was 15%",
    "paragraph": 2,
    "system_detected": true
  }
}
```

## Annotation Workflow

### Annotator Instructions

1. **Review Both Claims**: Read the two claims carefully
2. **Assess Relationship**:
   - `contradiction`: Claims directly contradict each other
   - `not_contradiction`: Claims are consistent or unrelated
   - `unsure`: Cannot determine relationship
3. **Add Notes** (Optional): Explain your reasoning
4. **Submit**: Click "Submit" to save annotation

### Quality Control

- **Target**: 100% consistency between annotators for contradictory pairs
- **Minimum Agreement**: Cohen's kappa ≥ 0.65
- **Dispute Resolution**: A third annotator resolves disagreements

## Exporting Results

### 1. Export Annotations from Label Studio
```bash
curl -X GET http://localhost:8080/api/projects/{project_id}/export?exportType=json \
  -H "Authorization: Token your_token_here" \
  > annotations_export.json
```

### 2. Process Exports
```bash
python process_label_studio_export.py --file annotations_export.json
```

This generates:
- Standardized annotation format
- Inter-annotator agreement metrics
- Cohen's kappa calculation

## Computing Inter-Annotator Agreement

### 1. Prepare Matched Annotations
```bash
python compute_agreement.py \
  --annotator1 annotator_1_export.json \
  --annotator2 annotator_2_export.json \
  --report-id report_001
```

### 2. Calculate Cohen's Kappa
```python
from evaluation_metrics import EvaluationMetrics

metrics = EvaluationMetrics()
agreement = metrics.calculate_inter_annotator_agreement(
    report_id="report_001",
    annotator_1="annotator_1",
    annotator_2="annotator_2"
)
print(f"Cohen's Kappa: {agreement['cohens_kappa']:.3f}")
```

### 3. Generate Report
```bash
python generate_agreement_report.py
```

Output: `results/inter_annotator_agreement.json`

## Dataset Structure

### Annotation Coverage
- **Total Reports**: 100
- **Reported Contradictions**: ~150-200 (system-detected)
- **Annotator Pairs**: 2 per report
- **Total Annotations**: 300-400

### Timeline
- Annotation Phase 1: Reports 1-50 (Annotators A & B)
- Annotation Phase 2: Reports 51-100 (Annotators A & B)
- Dispute Resolution: Any flagged disagreements

## Troubleshooting

### Issue: JSON Import Fails
**Solution**: Validate JSON format:
```bash
python -m json.tool annotation_tasks.json
```

### Issue: Conflicting Annotations
**Solution**: Check:
1. Both annotators completed their assigned reports
2. No duplicate assignments
3. Both annotated the same claim pairs

Use:
```bash
python validate_annotation_coverage.py
```

### Issue: Cohen's Kappa Cannot Be Computed
**Solution**: Ensure:
1. Minimum 2 matching annotations
2. Both annotators labeled same claim pairs
3. Labels are binary (0 or 1)

## API Integration

### Upload Annotations Programmatically
```python
from label_studio_sdk.client import LabelStudio

client = LabelStudio(url='http://localhost:8080', api_key='your_token')
project = client.projects.get(project_id=1)
project.import_tasks([task1, task2, ...])
```

### Export Annotations
```python
annotations = project.get_labeled_tasks()
for task in annotations:
    print(f"Task {task.id}: {task.annotations}")
```

## Next Steps

1. ✅ Setup Label Studio instance
2. ✅ Create project and configure labels
3. ✅ Import annotation tasks
4. ✅ Distribute to annotators
5. ⏳ Wait for completion
6. ✅ Export results
7. ✅ Calculate agreement metrics
8. ✅ Generate evaluation report

## Reference

- Label Studio Docs: https://labelstud.io/guide/
- API Docs: https://api.labelstud.io/
- Troubleshooting: https://labelstud.io/guide/troubleshooting.html
