# API Reference

Complete API documentation for the Insurance Supplementation Agent System.

## Base URL

```
http://localhost:8000/v1
```

## Authentication

Currently, the API does not require authentication. In production, implement one of:
- API Key authentication via `X-API-Key` header
- OAuth 2.0 Bearer tokens
- JWT tokens

## Content Types

- Request: `multipart/form-data` for file uploads, `application/json` for other endpoints
- Response: `application/json` (default), `application/pdf`, `text/html`

---

## Endpoints

### Create Job

Submit a new supplementation job for processing.

```
POST /v1/jobs
```

**Request** (multipart/form-data):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `estimate_pdf` | File | Yes | Insurance estimate PDF |
| `photos` | File[] | Yes | Job photos (1-20 images) |
| `metadata` | JSON string | Yes | Job metadata |
| `costs` | JSON string | Yes | Contractor costs |
| `targets` | JSON string | No | Business targets |
| `callback_url` | string | No | Webhook URL for completion |

**Metadata JSON Schema**:
```json
{
  "carrier": "State Farm",
  "claim_number": "CLM-12345",
  "insured_name": "John Doe",
  "property_address": "123 Main St, Dallas, TX 75201",
  "date_of_loss": "2024-01-15",
  "policy_number": "POL-999",
  "adjuster_name": "Jane Smith",
  "adjuster_email": "jane.smith@statefarm.com",
  "adjuster_phone": "555-123-4567"
}
```

**Costs JSON Schema**:
```json
{
  "materials_cost": 5000.00,
  "labor_cost": 8000.00,
  "other_costs": 500.00
}
```

**Targets JSON Schema** (optional):
```json
{
  "minimum_margin": 0.33
}
```

**Response** (202 Accepted):
```json
{
  "job_id": "job_abc123def456",
  "status": "queued",
  "created_at": "2024-01-15T10:30:00Z",
  "estimated_completion": "2024-01-15T10:35:00Z",
  "links": {
    "self": "/v1/jobs/job_abc123def456",
    "status": "/v1/jobs/job_abc123def456",
    "report": "/v1/jobs/job_abc123def456/report"
  }
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:8000/v1/jobs \
  -F "estimate_pdf=@estimate.pdf" \
  -F "photos=@photo1.jpg" \
  -F "photos=@photo2.jpg" \
  -F "photos=@photo3.jpg" \
  -F 'metadata={"carrier":"State Farm","claim_number":"CLM-123","insured_name":"John Doe","property_address":"123 Main St, Dallas, TX"}' \
  -F 'costs={"materials_cost":5000,"labor_cost":8000}' \
  -F 'targets={"minimum_margin":0.33}'
```

**Python Example**:
```python
import httpx

async def create_job():
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/v1/jobs",
            files=[
                ("estimate_pdf", open("estimate.pdf", "rb")),
                ("photos", open("photo1.jpg", "rb")),
                ("photos", open("photo2.jpg", "rb")),
            ],
            data={
                "metadata": '{"carrier":"State Farm","claim_number":"CLM-123","insured_name":"John Doe","property_address":"123 Main St"}',
                "costs": '{"materials_cost":5000,"labor_cost":8000}',
            }
        )
        return response.json()
```

---

### Get Job Status

Retrieve the status and results of a job.

```
GET /v1/jobs/{job_id}
```

**Parameters**:

| Parameter | Type | Description |
|-----------|------|-------------|
| `job_id` | path | Job identifier |
| `include` | query | Optional: `evidence`, `gaps`, `supplements`, `review` |

**Response** (200 OK):
```json
{
  "job_id": "job_abc123def456",
  "status": "completed",
  "stage": "completed",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:34:00Z",
  "completed_at": "2024-01-15T10:34:30Z",
  "results": {
    "supplement_total": 2450.00,
    "supplement_count": 8,
    "processing_time_seconds": 270.5,
    "llm_calls": 9,
    "review_cycles": 1
  },
  "links": {
    "self": "/v1/jobs/job_abc123def456",
    "report": "/v1/jobs/job_abc123def456/report"
  }
}
```

**Job Statuses**:

| Status | Description |
|--------|-------------|
| `queued` | Job is waiting to be processed |
| `processing` | Job is currently being processed |
| `completed` | Job completed successfully |
| `escalated` | Job requires human review |
| `approved` | Escalated job was approved |
| `rejected` | Escalated job was rejected |
| `failed` | Job processing failed |
| `cancelled` | Job was cancelled |

---

### List Jobs

List all jobs with optional filtering.

```
GET /v1/jobs
```

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `status` | string | - | Filter by status |
| `carrier` | string | - | Filter by carrier |
| `limit` | int | 20 | Max results (1-100) |
| `offset` | int | 0 | Pagination offset |

**Response** (200 OK):
```json
{
  "jobs": [
    {
      "job_id": "job_abc123def456",
      "status": "completed",
      "carrier": "State Farm",
      "created_at": "2024-01-15T10:30:00Z",
      "completed_at": "2024-01-15T10:34:30Z"
    }
  ],
  "pagination": {
    "limit": 20,
    "offset": 0,
    "total": 1
  }
}
```

---

### Download Report

Download the generated supplement report.

```
GET /v1/jobs/{job_id}/report
```

**Query Parameters**:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `format` | string | `pdf` | Output format: `pdf` or `html` |

**Response**:
- `application/pdf` - PDF document
- `text/html` - HTML document

**cURL Example**:
```bash
# Download PDF
curl -o report.pdf http://localhost:8000/v1/jobs/job_abc123/report

# Download HTML
curl -o report.html "http://localhost:8000/v1/jobs/job_abc123/report?format=html"
```

---

### Approve Job

Approve an escalated job for delivery.

```
POST /v1/jobs/{job_id}/approve
```

**Request Body**:
```json
{
  "approved_by": "John Manager",
  "notes": "Reviewed and approved after verifying photo evidence"
}
```

**Response** (200 OK):
```json
{
  "job_id": "job_abc123def456",
  "status": "approved",
  "message": "Job approved for delivery"
}
```

---

### Reject Job

Reject an escalated job.

```
POST /v1/jobs/{job_id}/reject
```

**Request Body**:
```json
{
  "rejected_by": "John Manager",
  "reason": "Insufficient photo evidence for supplement SUP-003"
}
```

**Response** (200 OK):
```json
{
  "job_id": "job_abc123def456",
  "status": "rejected"
}
```

---

### Cancel Job

Cancel a pending or processing job.

```
DELETE /v1/jobs/{job_id}
```

**Response** (200 OK):
```json
{
  "job_id": "job_abc123def456",
  "status": "cancelled"
}
```

---

### Health Check

Check API health status.

```
GET /health
```

**Response** (200 OK):
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "components": {
    "api": "healthy",
    "job_store": "healthy",
    "vision_model": "available",
    "text_model": "available"
  }
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "detail": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `INVALID_FILE_TYPE` | 400 | Uploaded file is not the expected type |
| `TOO_MANY_PHOTOS` | 400 | More than 20 photos uploaded |
| `INVALID_REQUEST` | 400 | Request validation failed |
| `INVALID_JSON` | 400 | JSON parsing failed |
| `MISSING_FIELDS` | 400 | Required fields missing |
| `JOB_NOT_FOUND` | 404 | Job ID does not exist |
| `REPORT_NOT_READY` | 404 | Report not yet generated |
| `INVALID_STATE` | 400 | Job is not in required state |
| `CANNOT_CANCEL` | 400 | Job cannot be cancelled |

---

## Webhooks

If `callback_url` is provided when creating a job, a POST request will be sent on completion:

```json
{
  "event": "job.completed",
  "job_id": "job_abc123def456",
  "status": "completed",
  "timestamp": "2024-01-15T10:34:30Z",
  "results": {
    "supplement_total": 2450.00,
    "supplement_count": 8
  }
}
```

Webhook events:
- `job.completed` - Job finished successfully
- `job.escalated` - Job requires human review
- `job.failed` - Job processing failed

---

## Rate Limits

| Tier | Requests/min | Concurrent Jobs |
|------|--------------|-----------------|
| Default | 60 | 5 |
| Pro | 300 | 20 |
| Enterprise | Unlimited | Unlimited |

Rate limit headers:
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 58
X-RateLimit-Reset: 1705315860
```

---

## OpenAPI Specification

Interactive API documentation is available at:
- Swagger UI: `http://localhost:8000/v1/docs`
- ReDoc: `http://localhost:8000/v1/redoc`
- OpenAPI JSON: `http://localhost:8000/v1/openapi.json`
