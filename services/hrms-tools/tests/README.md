# CV Analysis Service - Test Scripts

This directory contains test scripts for validating the CV Analysis Service.

## 📋 Available Tests

### `test_service.py`

Comprehensive test script that validates the entire service functionality:
- ✅ Health endpoint check
- ✅ CV analysis with sample data
- ✅ Response validation
- ✅ Support for multiple LLM providers

## 🚀 Quick Start

### 1. Install Dependencies

```bash
cd services/hrms-tools/tests
pip install -r requirements.txt
```

### 2. Start the Service

Make sure the CV Analysis Service is running:

```bash
# Option A: Using Docker
cd ..
docker-compose up -d

# Option B: Running locally
cd ..
python -m app.main
```

### 3. Run Tests

```bash
# Run all tests
python test_service.py

# Run health check only
python test_service.py --health-only

# Test with specific LLM provider
python test_service.py --provider openai
python test_service.py --provider anthropic
python test_service.py --provider gemini

# Test against different URL
python test_service.py --url http://my-server:8000
```

## 📖 Test Script Options

```
usage: test_service.py [-h] [--url URL] [--provider {auto,openai,anthropic,gemini}] [--health-only]

Test CV Analysis Service

optional arguments:
  -h, --help            show this help message and exit
  --url URL             Base URL of the service (default: http://localhost:8000)
  --provider {auto,openai,anthropic,gemini}
                        LLM provider to use (default: auto)
  --health-only         Only run health check, skip analysis
```

## 🎯 What the Test Does

### 1. Health Check

Tests the `/api/v1/health` endpoint:
- Verifies service is running
- Checks available LLM providers
- Displays configuration status

### 2. CV Analysis

Tests the `/api/v1/analyze` endpoint:
- Generates a realistic sample CV (PDF)
- Sends CV with position requirements and company criteria
- Validates response structure
- Displays analysis results including:
  - Overall score and recommendation
  - Section-wise scores with rationale
  - Key strengths identified
  - Critical gaps
  - Follow-up interview questions
  - Processing metadata

### 3. Output

The script provides:
- Colorized console output for easy reading
- Detailed results display
- Full JSON response saved to `test_analysis_result.json`
- Clear pass/fail status

## 📊 Sample Output

```
============================================================
CV Analysis Service - Test Script
============================================================

Service URL: http://localhost:8000
LLM Provider: auto

Testing Health Endpoint
URL: http://localhost:8000/api/v1/health
✓ Health check passed
  Status: healthy
  Version: 1.0.0
  LLM Providers:
    • openai: available
    • anthropic: available
    • gemini: not_configured

Testing CV Analysis Endpoint
URL: http://localhost:8000/api/v1/analyze
Creating sample CV...
  CV size: 12543 bytes
Sending analysis request (Provider: auto)...

✓ Analysis completed successfully

=== ANALYSIS RESULTS ===

Analysis ID: 550e8400-e29b-41d4-a716-446655440000
Overall Score: 78/100
Recommendation: strong_yes

Section Scores:

  Technical Skills
    Score: 85/100 (Weight: 40%)
    Weighted: 34.00
    Rationale: Strong Python background with 7 years experience...

  Experience
    Score: 80/100 (Weight: 30%)
    Weighted: 24.00
    Rationale: Progressive career growth with relevant experience...

...

Key Strengths:
  1. 7+ years of Python development experience
  2. Proven microservices architecture expertise
  3. Strong track record in high-traffic applications
  4. Leadership experience with team management
  5. Active continuous learner with relevant certifications

Critical Gaps:
  1. No explicit Kubernetes experience mentioned
  2. Limited mention of event-driven architectures

Follow-up Questions:
  1. Can you describe your experience with event-driven architectures?
  2. How do you approach database schema design for high-traffic applications?
  3. Tell us about a challenging architectural decision you made
  4. How do you stay updated with emerging technologies?

Analysis Metadata:
  Provider: openai
  Model: gpt-4-turbo-preview
  Tokens Used: 3450
  Processing Time: 2340ms
  CV Pages: 2

Full response saved to: test_analysis_result.json

============================================================
Test Summary
============================================================
Health Check: PASS
CV Analysis: PASS

✓ All tests passed!
```

## 🔍 Viewing Full Results

The complete analysis response is saved to `test_analysis_result.json`:

```bash
# View full JSON response
cat test_analysis_result.json

# Pretty print
python -m json.tool test_analysis_result.json
```

## 🛠️ Customizing Tests

### Testing with Your Own CV

Modify the `create_sample_cv()` function or replace it with:

```python
def load_cv_from_file(filepath: str) -> bytes:
    """Load CV from file"""
    with open(filepath, 'rb') as f:
        return f.read()

# Use it in test_analyze()
cv_bytes = load_cv_from_file('path/to/your/cv.pdf')
```

### Testing Different Position Requirements

Modify the `position_framework` in the `test_analyze()` function:

```python
"position_framework": {
    "role_title": "Your Position Title",
    "key_requirements": [
        "Your requirement 1",
        "Your requirement 2",
        # ...
    ],
    # ...
}
```

### Testing Different Company Criteria

Modify the `company_criteria` in the `test_analyze()` function:

```python
"company_criteria": {
    "company_name": "Your Company",
    "values": ["Value 1", "Value 2"],
    # ...
}
```

## 🧪 Advanced Testing

### Test All Providers

```bash
# Test each provider separately
for provider in openai anthropic gemini; do
    echo "Testing with $provider..."
    python test_service.py --provider $provider
done
```

### Integration with CI/CD

```bash
# Exit with proper status codes
python test_service.py && echo "Tests passed" || echo "Tests failed"
```

### Performance Testing

```bash
# Time the analysis
time python test_service.py
```

## 🐛 Troubleshooting

### Service not reachable

```
✗ Health check failed: Connection refused
```

**Solution:**
- Ensure service is running: `docker-compose ps` or check local process
- Verify URL is correct: `--url http://localhost:8000`
- Check firewall settings

### No LLM providers configured

```
LLM Providers:
  • openai: not_configured
  • anthropic: not_configured
  • gemini: not_configured
```

**Solution:**
- Set at least one API key in `.env` file
- Restart the service after adding API keys

### Analysis timeout

```
✗ Analysis failed: timeout
```

**Solution:**
- Increase timeout in script (default: 120s)
- Check LLM provider API status
- Try with a different provider: `--provider anthropic`

### PDF generation fails

```
ModuleNotFoundError: No module named 'reportlab'
```

**Solution:**
```bash
pip install -r requirements.txt
```

## 📝 Creating More Tests

You can create additional test scripts in this directory:

```python
#!/usr/bin/env python3
"""
Custom test for specific scenarios
"""

import requests
import json

def test_custom_scenario():
    """Test a specific use case"""
    # Your test logic here
    pass

if __name__ == "__main__":
    test_custom_scenario()
```

## 🤝 Contributing Tests

When adding new tests:
1. Follow the existing code style
2. Add clear documentation
3. Include usage examples
4. Update this README

## 📚 Related Documentation

- [Main Service README](../README.md)
- [API Documentation](http://localhost:8000/docs) (when service is running)
- [GitHub Actions Workflows](../../../.github/workflows/README.md)
