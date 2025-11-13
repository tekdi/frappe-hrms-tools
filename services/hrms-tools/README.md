# CV Analysis Service

AI-powered microservice for analyzing candidate CVs against position requirements and company criteria.

## 🎯 Features

- **Multi-LLM Support**: Works with OpenAI GPT-4, Anthropic Claude, and Google Gemini
- **Document Processing**: Handles PDF and DOCX files
- **Structured Analysis**: Returns detailed scores, strengths, gaps, and interview questions
- **Prompt Versioning**: Support for multiple prompt versions with easy A/B testing
- **Audit Logging**: Complete audit trail with SQLite database
- **RESTful API**: Clean, well-documented API with FastAPI
- **Docker Ready**: Easy deployment with Docker and docker-compose

## 📋 Table of Contents

- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Development](#development)
- [Testing](#testing)

## 🏗️ Architecture

```
┌─────────────────────────────────────────┐
│          FastAPI Application            │
├─────────────────────────────────────────┤
│  ┌────────────┐  ┌──────────────────┐   │
│  │  Document  │  │   CV Analyzer    │   │
│  │   Parser   │→ │   Orchestrator   │   │
│  └────────────┘  └──────────────────┘   │
│                          ↓               │
│  ┌───────────────────────────────────┐  │
│  │      LLM Provider Factory         │  │
│  ├───────────┬───────────┬──────────┤  │
│  │  OpenAI   │ Anthropic │  Gemini  │  │
│  └───────────┴───────────┴──────────┘  │
│                          ↓               │
│  ┌───────────────────────────────────┐  │
│  │      Prompt Manager (v1, v2...)   │  │
│  └───────────────────────────────────┘  │
│                          ↓               │
│  ┌───────────────────────────────────┐  │
│  │      Audit Logger (SQLite)        │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

## 🚀 Installation

### Prerequisites

- Python 3.11+
- Docker (optional, for containerized deployment)
- At least one LLM API key (OpenAI, Anthropic, or Gemini)

### Local Installation

1. **Clone the repository**
```bash
cd services/hrms-tools
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

5. **Run the service**
```bash
python -m app.main
# Or using uvicorn directly:
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Docker Installation

1. **Configure environment**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

2. **Build and run with docker-compose**
```bash
docker-compose up -d
```

3. **Check logs**
```bash
docker-compose logs -f
```

## ⚙️ Configuration

### Environment Variables

All configuration is done via environment variables. See `.env.example` for all available options.

**Key Configuration:**

```bash
# Choose your LLM provider
DEFAULT_LLM_PROVIDER=auto  # or openai, anthropic, gemini

# Add API keys (at least one required)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GEMINI_API_KEY=...
```

### LLM Provider Selection

The service automatically selects an available provider based on:

1. **Request-level**: Specify provider in API request
2. **Environment-level**: Set `DEFAULT_LLM_PROVIDER`
3. **Auto-detection**: Uses first available provider with valid API key

## 📖 Usage

### Quick Start Example

```python
import requests
import base64

# Read CV file
with open("candidate_cv.pdf", "rb") as f:
    cv_base64 = base64.b64encode(f.read()).decode()

# Prepare request
payload = {
    "cv_file": cv_base64,
    "cv_filename": "candidate_cv.pdf",
    "position_framework": {
        "role_title": "Senior Backend Engineer",
        "key_requirements": [
            "5+ years Python experience",
            "Microservices architecture",
            "Database design"
        ],
        "scoring_weights": {
            "technical_skills": 40,
            "experience": 30,
            "education": 15,
            "cultural_fit": 15
        },
        "must_have_skills": ["Python", "REST API"],
        "nice_to_have_skills": ["Docker", "Kubernetes"]
    },
    "company_criteria": {
        "company_name": "ACME Corp",
        "values": ["Innovation", "Collaboration", "Ownership"],
        "evaluation_guidelines": "Focus on problem-solving ability",
        "disqualifiers": ["Less than 3 years experience"]
    },
    "config": {
        "llm_provider": "openai",  # or "anthropic", "gemini", "auto"
        "prompt_version": "v1",
        "analysis_depth": "detailed"
    }
}

# Make request
response = requests.post(
    "http://localhost:8000/api/v1/analyze",
    json=payload
)

result = response.json()
print(f"Overall Score: {result['overall_score']}")
print(f"Recommendation: {result['recommendation']}")
```

### cURL Example

```bash
curl -X POST "http://localhost:8000/api/v1/analyze" \
  -H "Content-Type: application/json" \
  -d @request.json
```

## 🔌 API Documentation

Once the service is running, access interactive API documentation:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Main Endpoints

#### `POST /api/v1/analyze`

Analyze a CV against position and company criteria.

**Request Body:**
```json
{
  "cv_file": "base64_encoded_cv",
  "cv_filename": "john_doe.pdf",
  "position_framework": { ... },
  "company_criteria": { ... },
  "config": { ... }
}
```

**Response:**
```json
{
  "analysis_id": "uuid",
  "timestamp": "2025-11-13T10:30:00Z",
  "overall_score": 78,
  "recommendation": "strong_yes",
  "section_scores": [...],
  "key_strengths": [...],
  "critical_gaps": [...],
  "follow_up_questions": [...],
  "metadata": { ... }
}
```

#### `GET /api/v1/health`

Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "llm_providers": {
    "openai": "available",
    "anthropic": "available",
    "gemini": "not_configured"
  }
}
```

## 🛠️ Development

### Project Structure

```
services/hrms-tools/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── analyze.py       # API endpoints
│   ├── core/
│   │   ├── config.py            # Configuration
│   │   ├── llm_factory.py       # LLM provider factory
│   │   └── prompt_manager.py    # Prompt versioning
│   ├── llm_providers/
│   │   ├── base.py              # Base provider class
│   │   ├── openai_provider.py   # OpenAI implementation
│   │   ├── anthropic_provider.py # Anthropic implementation
│   │   └── gemini_provider.py   # Gemini implementation
│   ├── models/
│   │   ├── request.py           # Request models
│   │   └── response.py          # Response models
│   ├── services/
│   │   ├── document_parser.py   # PDF/DOCX parser
│   │   ├── cv_analyzer.py       # Main analyzer
│   │   └── audit_logger.py      # Audit logging
│   ├── prompts/
│   │   └── v1_analysis.txt      # Prompt templates
│   └── main.py                  # FastAPI app
├── database/                    # SQLite audit logs
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

### Adding a New Prompt Version

1. Create new prompt file: `app/prompts/v2_analysis.txt`
2. Update `prompt_manager.py` if needed
3. Use in requests: `"config": {"prompt_version": "v2"}`

### Adding a New LLM Provider

1. Create provider class in `app/llm_providers/`
2. Inherit from `BaseLLMProvider`
3. Implement required methods
4. Add to `llm_factory.py`
5. Add configuration to `config.py`

## 🧪 Testing

### Manual Testing

```bash
# Check health
curl http://localhost:8000/api/v1/health

# Test with sample CV
python scripts/test_analysis.py
```

### Viewing Audit Logs

The service logs all analyses to `database/audit_logs.db`. You can query it:

```bash
sqlite3 database/audit_logs.db

# View recent analyses
SELECT analysis_id, cv_filename, overall_score, recommendation, timestamp
FROM cv_analysis_logs
ORDER BY timestamp DESC
LIMIT 10;

# View token usage
SELECT * FROM token_usage ORDER BY date DESC;
```

## 🔒 Security Notes

- API keys are stored in environment variables (never in code)
- Audit logs track all operations
- Input validation on all requests
- File size limits enforced
- No CV content stored permanently (only audit metadata)

## 📊 Monitoring

### Health Check

```bash
curl http://localhost:8000/api/v1/health
```

### Logs

```bash
# Docker logs
docker-compose logs -f cv-analysis-service

# Local logs
# Check console output
```

### Metrics

Access audit database to view:
- Total analyses performed
- Token usage by provider
- Average processing times
- Error rates

## 🐛 Troubleshooting

### No LLM providers available

**Error**: "No LLM providers are configured"

**Solution**: Ensure at least one API key is set in `.env`:
```bash
OPENAI_API_KEY=sk-...
# or
ANTHROPIC_API_KEY=sk-ant-...
# or
GEMINI_API_KEY=...
```

### PDF parsing fails

**Error**: "No text could be extracted from PDF"

**Solution**: PDF may be scanned/image-based. Consider adding OCR support or requesting text-based CVs.

### Docker build fails

**Solution**:
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

## 📝 License

See LICENSE file for details.

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📧 Support

For issues and questions, please use the GitHub issue tracker.
