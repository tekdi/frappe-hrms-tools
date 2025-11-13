# CV Analyzer - Frappe HRMS Integration

AI-powered CV analysis integration for Frappe HRMS. This app connects your Frappe HRMS instance with the CV Analysis microservice to automatically analyze candidate resumes and provide structured evaluation results.

## Features

- **Automatic CV Analysis**: Automatically analyzes CVs when uploaded to Job Applicant
- **Position-Specific Frameworks**: Define evaluation criteria for each job opening
- **Company-Wide Standards**: Maintain consistent evaluation standards across all positions
- **Detailed Scoring**: Multi-dimensional scoring with strengths, gaps, and interview questions
- **Real-time Updates**: Live progress updates during analysis
- **Email Notifications**: Automatic notifications when analysis completes
- **Rich UI Integration**: Analysis results displayed directly in Job Applicant form

## Prerequisites

- Frappe Framework v14 or v15
- Frappe HRMS app installed
- CV Analysis Microservice running (see `services/hrms-tools/`)
- Python 3.10+

## Installation

### 1. Get the App

```bash
cd /path/to/your/frappe-bench
bench get-app https://github.com/tekdi/frappe-hrms-tools --branch main
```

### 2. Install to Site

```bash
bench --site your-site-name install-app cv_analyzer
```

### 3. Migrate

```bash
bench --site your-site-name migrate
```

### 4. Clear Cache

```bash
bench --site your-site-name clear-cache
bench restart
```

## Configuration

### 1. Set up CV Analysis Service

Navigate to:
**Setup > CV Analyzer > CV Analysis Settings**

Configure:
- **Service URL**: URL of your CV Analysis microservice (e.g., `http://localhost:8000`)
- **API Version**: Usually `v1`
- **Default LLM Provider**: Choose from `auto`, `openai`, `anthropic`, or `gemini`
- **Auto-analyze on CV Upload**: Enable/disable automatic analysis
- **Show Analysis in Dashboard**: Display results in dashboard

### 2. Configure Company Evaluation Criteria

Navigate to:
**Setup > CV Analyzer > Company Evaluation Criteria**

Set up:
- Company name
- Core values
- General evaluation guidelines
- Disqualifying criteria
- Preferred backgrounds

### 3. Create Position Evaluation Frameworks

For each job opening, create a Position Evaluation Framework:

Navigate to:
**CV Analyzer > Position Frameworks > New**

Define:
- Link to Job Opening
- Key requirements for the role
- Must-have skills
- Nice-to-have skills
- Scoring weights for different sections
- Minimum years of experience

## Usage

### Automatic Analysis

When auto-analysis is enabled in settings:

1. Create or edit a Job Applicant
2. Upload a resume (PDF or DOCX)
3. Save the document
4. Analysis is automatically queued
5. Receive real-time notification when complete
6. View results in the Job Applicant form

### Manual Analysis

To trigger analysis manually:

1. Open a Job Applicant with a resume attached
2. Click **Actions > Analyze CV**
3. Wait for analysis to complete
4. Click **View > View CV Analysis**

### Viewing Results

**In Job Applicant Form:**
- Analysis summary displayed at the top with overall score and recommendation
- Click "View Full Analysis" to see detailed results

**In CV Analysis Result:**
- Overall score and recommendation
- Section-wise scores with rationale
- Key strengths identified
- Critical gaps
- Suggested follow-up interview questions
- Analysis metadata (provider, tokens, processing time)

## DocTypes

### CV Analysis Settings (Single)

Configuration for the CV Analysis service connection and automation settings.

**Fields:**
- Service URL
- API Version
- Default LLM Provider
- Default Prompt Version
- Auto-analyze on CV Upload
- Show Analysis in Dashboard

### Company Evaluation Criteria (Single)

Company-wide evaluation standards applied to all positions.

**Fields:**
- Company Name
- Company Core Values
- Evaluation Guidelines
- Disqualifying Criteria
- Preferred Backgrounds

### Position Evaluation Framework

Position-specific evaluation criteria linked to Job Openings.

**Fields:**
- Job Opening (Link)
- Role Title
- Key Requirements
- Must-Have Skills
- Nice-to-Have Skills
- Scoring Weights (Technical Skills, Experience, Education, Cultural Fit)
- Minimum Years of Experience

### CV Analysis Result

Stores the analysis results for each job applicant.

**Fields:**
- Job Applicant (Link)
- Analysis Date
- Overall Score
- Recommendation (strong_yes, yes, maybe, no, strong_no)
- LLM Provider
- Tokens Used
- Processing Time
- Section Scores (Child Table)
- Insights (Child Table - Strengths, Gaps, Questions)

### CV Score Section (Child Table)

Individual section scores within an analysis.

**Fields:**
- Section
- Score
- Weight
- Weighted Score
- Rationale

### CV Analysis Insight (Child Table)

Insights from the analysis (strengths, gaps, questions).

**Fields:**
- Insight Type (Strength / Gap / Follow-up Question)
- Description

## API Methods

### `cv_analyzer.api.job_applicant.trigger_manual_analysis`

Manually trigger CV analysis for a job applicant.

**Parameters:**
- `job_applicant` (str): Job Applicant docname

**Returns:**
```python
{
    "message": "CV analysis has been queued",
    "status": "queued"
}
```

### `cv_analyzer.api.job_applicant.get_latest_analysis`

Get the latest CV analysis for a job applicant.

**Parameters:**
- `job_applicant` (str): Job Applicant docname

**Returns:**
- CV Analysis Result document dict or None

## Realtime Events

The app emits the following realtime events:

### `cv_analysis_progress`
Emitted when analysis starts.

```javascript
{
    "status": "started",
    "applicant": "JOB-APP-2025-00001"
}
```

### `cv_analysis_complete`
Emitted when analysis completes successfully.

```javascript
{
    "applicant": "JOB-APP-2025-00001",
    "analysis": "CVA-JOB-APP-2025-00001-0001",
    "score": 78,
    "recommendation": "strong_yes"
}
```

### `cv_analysis_failed`
Emitted when analysis fails.

```javascript
{
    "applicant": "JOB-APP-2025-00001",
    "error": "Error message"
}
```

## Troubleshooting

### Analysis Not Triggered

**Problem**: CV uploaded but analysis doesn't start

**Solutions:**
1. Check CV Analysis Settings - ensure auto-analysis is enabled
2. Verify Service URL is correct and service is running
3. Check background jobs: `bench --site your-site-name doctor`
4. Check Error Log doctype for errors

### Service Connection Failed

**Problem**: "CV analysis failed" error

**Solutions:**
1. Verify microservice is running:
   ```bash
   curl http://your-service-url/api/v1/health
   ```
2. Check Service URL in CV Analysis Settings
3. Ensure network connectivity between Frappe and microservice
4. Check microservice logs

### No LLM Provider Available

**Problem**: Analysis fails with "No LLM providers configured"

**Solutions:**
1. Ensure CV Analysis microservice has at least one API key configured
2. Check microservice .env file
3. Restart microservice after adding API keys

### File Read Error

**Problem**: "Could not read CV file"

**Solutions:**
1. Ensure file permissions are correct
2. Check if file exists in private/files or public/files
3. Verify file is PDF or DOCX format

## Development

### Local Development Setup

```bash
# Start Frappe bench
cd /path/to/frappe-bench
bench start

# In another terminal, start the microservice
cd services/hrms-tools
docker-compose up

# Access your site
http://localhost:8000
```

### Running Tests

```bash
bench --site your-site-name run-tests --app cv_analyzer
```

### Modifying the App

After making changes to DocTypes:

```bash
bench --site your-site-name migrate
bench --site your-site-name clear-cache
```

After changing JavaScript files:

```bash
bench build --app cv_analyzer
# OR for development
bench watch
```

## Architecture

```
┌─────────────────────────────────────────────┐
│           Frappe HRMS                       │
│  ┌───────────────────────────────────────┐  │
│  │  Job Applicant (with CV)              │  │
│  └────────────┬──────────────────────────┘  │
│               │ On Save Hook                 │
│               ▼                              │
│  ┌───────────────────────────────────────┐  │
│  │  CV Analyzer Integration              │  │
│  │  - Extract CV                         │  │
│  │  - Get Position Framework             │  │
│  │  - Get Company Criteria               │  │
│  └────────────┬──────────────────────────┘  │
│               │ HTTP POST                    │
└───────────────┼──────────────────────────────┘
                │
                ▼
┌───────────────────────────────────────────────┐
│     CV Analysis Microservice                  │
│     (FastAPI + Multi-LLM)                     │
└────────────┬──────────────────────────────────┘
             │ JSON Response
             ▼
┌─────────────────────────────────────────────┐
│           Frappe HRMS                       │
│  ┌───────────────────────────────────────┐  │
│  │  CV Analysis Result                   │  │
│  │  - Scores                             │  │
│  │  - Strengths & Gaps                   │  │
│  │  - Interview Questions                │  │
│  └───────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
```

## Security Considerations

- API keys for LLM providers stored in microservice, not in Frappe
- CV content not permanently stored in microservice
- Only metadata stored in audit logs
- File access respects Frappe permissions
- Analysis results inherit Job Applicant permissions

## License

MIT License - Copyright (c) 2025 TEKDI

## Support

For issues and questions:
- GitHub Issues: https://github.com/tekdi/frappe-hrms-tools/issues
- Documentation: https://github.com/tekdi/frappe-hrms-tools

## Related Documentation

- [CV Analysis Microservice](../../services/hrms-tools/README.md)
- [Frappe Framework](https://frappeframework.com/docs)
- [Frappe HRMS](https://github.com/frappe/hrms)
