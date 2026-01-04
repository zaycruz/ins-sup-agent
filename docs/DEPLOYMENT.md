# Deployment Guide

Production deployment documentation for the Insurance Supplementation Agent System.

## Deployment Options

| Option | Best For | Complexity |
|--------|----------|------------|
| Docker | Single server, development | Low |
| Docker Compose | Multi-container, staging | Medium |
| Kubernetes | Production, scaling | High |
| Cloud Run / Lambda | Serverless, auto-scaling | Medium |

---

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy project files
COPY pyproject.toml uv.lock ./
COPY src/ ./src/
COPY main.py ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Expose port
EXPOSE 8000

# Run server
CMD ["uv", "run", "uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Build and Run

```bash
# Build image
docker build -t ins-sup-agent:latest .

# Run container
docker run -d \
  --name ins-sup-agent \
  -p 8000:8000 \
  -e LLM_PROVIDER=openai \
  -e OPENAI_API_KEY=sk-your-key \
  ins-sup-agent:latest

# View logs
docker logs -f ins-sup-agent
```

---

## Docker Compose

### docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LLM_PROVIDER=${LLM_PROVIDER:-mock}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - VISION_MODEL=${VISION_MODEL:-gpt-4o}
      - TEXT_MODEL=${TEXT_MODEL:-gpt-4o}
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  redis_data:
```

### Run with Compose

```bash
# Start services
docker-compose up -d

# Scale API
docker-compose up -d --scale api=3

# View logs
docker-compose logs -f api
```

---

## Environment Variables

### Required for Production

| Variable | Description | Example |
|----------|-------------|---------|
| `LLM_PROVIDER` | LLM provider | `openai` |
| `OPENAI_API_KEY` | OpenAI API key | `sk-...` |
| `ANTHROPIC_API_KEY` | Anthropic API key | `sk-ant-...` |

### Optional Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `API_HOST` | `0.0.0.0` | API bind address |
| `API_PORT` | `8000` | API port |
| `VISION_MODEL` | `gpt-4o` | Vision analysis model |
| `TEXT_MODEL` | `gpt-4o` | Text processing model |
| `MAX_REVIEW_CYCLES` | `2` | Max review iterations |
| `MAX_PHOTOS` | `20` | Max photos per job |
| `DEFAULT_MARGIN_TARGET` | `0.33` | Default profit margin |
| `LOG_LEVEL` | `INFO` | Logging level |

### Production .env Example

```bash
# Production environment
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-prod-key-here

# Models
VISION_MODEL=gpt-4o
TEXT_MODEL=gpt-4o

# Server
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false

# Processing
MAX_REVIEW_CYCLES=2
MAX_PHOTOS=20
DEFAULT_MARGIN_TARGET=0.33

# Logging
LOG_LEVEL=WARNING
```

---

## Kubernetes Deployment

### deployment.yaml

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: ins-sup-agent
  labels:
    app: ins-sup-agent
spec:
  replicas: 3
  selector:
    matchLabels:
      app: ins-sup-agent
  template:
    metadata:
      labels:
        app: ins-sup-agent
    spec:
      containers:
      - name: api
        image: ins-sup-agent:latest
        ports:
        - containerPort: 8000
        env:
        - name: LLM_PROVIDER
          valueFrom:
            secretKeyRef:
              name: ins-sup-secrets
              key: llm-provider
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: ins-sup-secrets
              key: openai-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "2Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: ins-sup-agent
spec:
  selector:
    app: ins-sup-agent
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### secrets.yaml

```yaml
apiVersion: v1
kind: Secret
metadata:
  name: ins-sup-secrets
type: Opaque
stringData:
  llm-provider: "openai"
  openai-api-key: "sk-your-key"
```

---

## Scaling Considerations

### Horizontal Scaling

```
┌─────────────────────────────────────────┐
│            Load Balancer                 │
└─────────────────┬───────────────────────┘
                  │
    ┌─────────────┼─────────────┐
    ▼             ▼             ▼
┌───────┐    ┌───────┐    ┌───────┐
│ API 1 │    │ API 2 │    │ API 3 │
└───────┘    └───────┘    └───────┘
    │             │             │
    └─────────────┼─────────────┘
                  ▼
         ┌───────────────┐
         │  Redis Queue  │
         └───────────────┘
```

### Resource Requirements

| Component | CPU | Memory | Notes |
|-----------|-----|--------|-------|
| API (per instance) | 0.5-1 core | 512MB-2GB | Scales with traffic |
| Job Worker | 1-2 cores | 2-4GB | LLM calls are memory-intensive |
| Redis | 0.25 core | 256MB | Job queue storage |

### Auto-scaling Rules

```yaml
# HorizontalPodAutoscaler
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: ins-sup-agent-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: ins-sup-agent
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

---

## Monitoring

### Health Endpoints

| Endpoint | Purpose | Expected Response |
|----------|---------|-------------------|
| `/health` | Liveness probe | `{"status": "healthy"}` |
| `/ready` | Readiness probe | `{"ready": true}` |

### Recommended Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `jobs_created_total` | Counter | Total jobs submitted |
| `jobs_completed_total` | Counter | Successfully completed |
| `jobs_failed_total` | Counter | Failed jobs |
| `job_processing_seconds` | Histogram | Processing time |
| `llm_calls_total` | Counter | LLM API calls |
| `llm_latency_seconds` | Histogram | LLM response time |

### Prometheus Configuration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'ins-sup-agent'
    static_configs:
      - targets: ['ins-sup-agent:8000']
    metrics_path: '/metrics'
```

### Logging

```python
# Structured JSON logging
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        return json.dumps({
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "job_id": getattr(record, "job_id", None)
        })
```

---

## Security Best Practices

### API Security

1. **Enable HTTPS**: Use TLS termination at load balancer
2. **Authentication**: Implement API key or OAuth
3. **Rate Limiting**: Prevent abuse with rate limits
4. **Input Validation**: All inputs validated via Pydantic

### Secret Management

```bash
# Never commit secrets to git
# Use environment variables or secret managers

# AWS Secrets Manager
aws secretsmanager get-secret-value --secret-id ins-sup-agent/prod

# HashiCorp Vault
vault kv get secret/ins-sup-agent
```

### Network Security

```yaml
# Kubernetes NetworkPolicy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ins-sup-agent-network
spec:
  podSelector:
    matchLabels:
      app: ins-sup-agent
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - podSelector:
        matchLabels:
          app: ingress-nginx
    ports:
    - port: 8000
  egress:
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0  # Allow LLM API access
    ports:
    - port: 443
```

### Audit Logging

```python
# Log all job operations
logger.info("Job created", extra={
    "job_id": job_id,
    "carrier": metadata.carrier,
    "user_ip": request.client.host,
    "action": "create"
})
```

---

## Backup and Recovery

### Data to Backup

| Data | Location | Frequency |
|------|----------|-----------|
| Job store | In-memory / Redis | Real-time (use persistent Redis) |
| Reports | Generated per job | Store in S3/GCS |
| Logs | Container stdout | Stream to log aggregator |

### Disaster Recovery

1. **Multi-region**: Deploy to multiple regions
2. **Database replication**: If using persistent storage
3. **Report storage**: Replicate to multiple buckets

---

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Job stuck in `processing` | LLM timeout | Check LLM API status, increase timeout |
| `OPENAI_API_KEY not set` | Missing env var | Set environment variable |
| High memory usage | Large photos | Limit photo size, add memory |
| Slow processing | Model selection | Use faster model for non-critical tasks |

### Debug Mode

```bash
# Enable debug logging
LOG_LEVEL=DEBUG uv run python main.py

# Check LLM connectivity
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
  https://api.openai.com/v1/models
```
