# Insurance Supplementation Agent System

A multi-agent AI system that automates roofing insurance supplement generation by analyzing photos, parsing estimates, identifying coverage gaps, and producing carrier-ready supplement packages.

## Features

- **Vision Analysis**: AI-powered detection of roofing components and damage from photos
- **Estimate Parsing**: Automatic extraction of line items from any estimate format (Xactimate, Symbility, etc.)
- **Gap Analysis**: Cross-references visual evidence against estimate coverage
- **Supplement Strategy**: Generates defensible supplements with code citations and justifications
- **Review Loop**: Self-critiquing review cycle with automatic refinement
- **Report Generation**: Professional HTML/PDF reports ready for carrier submission
- **REST API**: Full-featured API for integration with existing systems

## Quick Start

### Prerequisites

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) package manager

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/ins-sup-agent.git
cd ins-sup-agent

# Install dependencies
uv sync

# Copy environment configuration
cp .env.example .env

# Edit .env with your API keys
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-your-key-here
```

### Running the Server

```bash
# Development mode with auto-reload
uv run python main.py

# Or using uvicorn directly
uv run uvicorn src.api.app:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000` with documentation at `http://localhost:8000/v1/docs`.

### Submit Your First Job

```bash
curl -X POST http://localhost:8000/v1/jobs \
  -F "estimate_pdf=@estimate.pdf" \
  -F "photos=@photo1.jpg" \
  -F "photos=@photo2.jpg" \
  -F 'metadata={"carrier":"State Farm","claim_number":"CLM-123","insured_name":"John Doe","property_address":"123 Main St"}' \
  -F 'costs={"materials_cost":5000,"labor_cost":8000}'
```

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Gateway                               │
│                    POST /v1/jobs                                 │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Orchestrator                                │
│  Coordinates agent pipeline and manages review loop              │
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│   Vision    │   │  Estimate   │   │     ...     │
│   Agent     │   │   Agent     │   │             │
└─────────────┘   └─────────────┘   └─────────────┘
```

### Agent Pipeline

| Agent | Purpose |
|-------|---------|
| **Vision Agent** | Analyzes photos to detect roofing components and damage |
| **Estimate Agent** | Parses insurance estimate PDF into structured line items |
| **Gap Analysis Agent** | Identifies discrepancies between evidence and estimate |
| **Strategist Agent** | Converts gaps into defensible supplement proposals |
| **Review Agent** | Self-critiques and requests refinements |
| **Report Agent** | Generates carrier-ready HTML/PDF reports |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/v1/jobs` | Submit a new supplementation job |
| `GET` | `/v1/jobs` | List jobs with filtering |
| `GET` | `/v1/jobs/{id}` | Get job status and results |
| `GET` | `/v1/jobs/{id}/report` | Download generated report |
| `POST` | `/v1/jobs/{id}/approve` | Approve an escalated job |
| `POST` | `/v1/jobs/{id}/reject` | Reject an escalated job |
| `DELETE` | `/v1/jobs/{id}` | Cancel a pending job |
| `GET` | `/health` | Health check |

See [docs/API.md](docs/API.md) for complete API documentation.

## Configuration

Configuration is managed through environment variables. See `.env.example` for all options.

### Key Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_PROVIDER` | `mock` | LLM provider: `openai`, `anthropic`, or `mock` |
| `OPENAI_API_KEY` | - | OpenAI API key |
| `ANTHROPIC_API_KEY` | - | Anthropic API key |
| `VISION_MODEL` | `gpt-4o` | Model for vision analysis |
| `TEXT_MODEL` | `gpt-4o` | Model for text processing |
| `DEFAULT_MARGIN_TARGET` | `0.33` | Default profit margin target (33%) |
| `API_PORT` | `8000` | API server port |

## Project Structure

```
ins-sup-agent/
├── src/
│   ├── agents/          # Agent implementations
│   ├── api/             # FastAPI application
│   ├── llm/             # LLM client abstractions
│   ├── orchestrator/    # Pipeline orchestration
│   ├── prompts/         # Agent system prompts
│   ├── schemas/         # Pydantic data models
│   ├── tools/           # Agent tools (code lookup, examples)
│   └── utils/           # Utilities (PDF extraction)
├── docs/                # Documentation
├── main.py              # Entry point
├── pyproject.toml       # Dependencies
└── .env.example         # Environment template
```

## Development

### Running Tests

```bash
uv run pytest
```

### Code Formatting

```bash
uv run ruff format src/
uv run ruff check src/ --fix
```

### Type Checking

```bash
uv run mypy src/
```

## Documentation

- [API Reference](docs/API.md)
- [Architecture Guide](docs/ARCHITECTURE.md)
- [Agent Details](docs/AGENTS.md)
- [Deployment Guide](docs/DEPLOYMENT.md)

## License

MIT License - see LICENSE file for details.
