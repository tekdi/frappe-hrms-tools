#!/usr/bin/env python3
"""
Test script for CV Analysis Service

This script tests the CV Analysis Service locally by:
1. Checking service health
2. Creating a sample CV
3. Sending it for analysis (base64 or multipart upload)
4. Validating the response

Usage:
    python test_service.py [--url URL] [--provider PROVIDER] [--method METHOD]

Examples:
    python test_service.py
    python test_service.py --url http://localhost:8000
    python test_service.py --provider anthropic
    python test_service.py --method multipart
    python test_service.py --method both
"""

import requests
import base64
import json
import sys
import argparse
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from typing import Dict, Any


class Colors:
    """ANSI color codes for terminal output"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'


def create_sample_cv() -> bytes:
    """
    Create a sample CV PDF for testing

    Returns:
        PDF bytes
    """
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # Title
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 50, "John Doe")

    c.setFont("Helvetica", 12)
    c.drawString(50, height - 70, "Senior Software Engineer")
    c.drawString(50, height - 85, "Email: john.doe@example.com | Phone: +1-555-0123")

    # Professional Summary
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 120, "Professional Summary")
    c.setFont("Helvetica", 11)

    summary = [
        "Experienced Senior Backend Engineer with 7+ years of expertise in Python,",
        "microservices architecture, and distributed systems. Proven track record in",
        "designing and implementing scalable solutions for high-traffic applications.",
        "Strong background in REST API development, database optimization, and cloud",
        "infrastructure. Passionate about clean code and software architecture."
    ]

    y = height - 140
    for line in summary:
        c.drawString(50, y, line)
        y -= 15

    # Technical Skills
    y -= 20
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Technical Skills")
    c.setFont("Helvetica", 11)

    skills = [
        "Languages: Python, JavaScript, SQL",
        "Frameworks: FastAPI, Django, Flask, React",
        "Databases: PostgreSQL, MongoDB, Redis",
        "Tools: Docker, Git, Jenkins, AWS",
        "Architecture: Microservices, REST APIs, Event-driven systems"
    ]

    y -= 20
    for skill in skills:
        c.drawString(50, y, f"• {skill}")
        y -= 15

    # Professional Experience
    y -= 20
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Professional Experience")

    # Job 1
    y -= 25
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Senior Backend Engineer | TechCorp Inc.")
    y -= 15
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(50, y, "Jan 2020 - Present (4+ years)")
    y -= 20
    c.setFont("Helvetica", 11)

    experience1 = [
        "• Architected and implemented microservices platform handling 10M+ requests/day",
        "• Led team of 5 engineers in migrating monolithic application to microservices",
        "• Designed and developed RESTful APIs used by 50+ client applications",
        "• Optimized database queries resulting in 60% performance improvement",
        "• Implemented CI/CD pipeline reducing deployment time by 80%"
    ]

    for exp in experience1:
        c.drawString(50, y, exp)
        y -= 15

    # Job 2
    y -= 10
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Backend Engineer | StartupXYZ")
    y -= 15
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(50, y, "Jun 2017 - Dec 2019 (2.5 years)")
    y -= 20
    c.setFont("Helvetica", 11)

    experience2 = [
        "• Built backend services for e-commerce platform using Python and PostgreSQL",
        "• Developed payment processing integration with Stripe and PayPal",
        "• Implemented caching strategy with Redis improving response time by 40%",
        "• Collaborated with frontend team on API design and documentation"
    ]

    for exp in experience2:
        if y < 100:  # Start new page if needed
            c.showPage()
            y = height - 50
        c.drawString(50, y, exp)
        y -= 15

    # Education
    y -= 20
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Education")
    y -= 20
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Bachelor of Science in Computer Science")
    y -= 15
    c.setFont("Helvetica", 11)
    c.drawString(50, y, "University of Technology | 2013 - 2017 | GPA: 3.8/4.0")

    # Certifications
    y -= 30
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, "Certifications")
    y -= 20
    c.setFont("Helvetica", 11)
    c.drawString(50, y, "• AWS Certified Solutions Architect - Associate")
    y -= 15
    c.drawString(50, y, "• Python for Data Science (Coursera)")

    c.save()
    buffer.seek(0)
    return buffer.read()


def test_health(base_url: str) -> bool:
    """
    Test the health endpoint

    Args:
        base_url: Base URL of the service

    Returns:
        True if healthy, False otherwise
    """
    print(f"\n{Colors.BOLD}Testing Health Endpoint{Colors.END}")
    print(f"{Colors.BLUE}URL: {base_url}/api/v1/health{Colors.END}")

    try:
        response = requests.get(f"{base_url}/api/v1/health", timeout=10)
        response.raise_for_status()

        data = response.json()
        print(f"{Colors.GREEN}✓ Health check passed{Colors.END}")
        print(f"  Status: {data.get('status')}")
        print(f"  Version: {data.get('version')}")
        print(f"  LLM Providers:")
        for provider, status in data.get('llm_providers', {}).items():
            status_color = Colors.GREEN if status == 'available' else Colors.YELLOW
            print(f"    • {provider}: {status_color}{status}{Colors.END}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"{Colors.RED}✗ Health check failed: {e}{Colors.END}")
        return False


def test_analyze(base_url: str, llm_provider: str = "auto") -> bool:
    """
    Test the CV analysis endpoint (Base64 method)

    Args:
        base_url: Base URL of the service
        llm_provider: LLM provider to use

    Returns:
        True if successful, False otherwise
    """
    print(f"\n{Colors.BOLD}Testing CV Analysis Endpoint (Base64){Colors.END}")
    print(f"{Colors.BLUE}URL: {base_url}/api/v1/analyze{Colors.END}")

    # Create sample CV
    print("Creating sample CV...")
    cv_bytes = create_sample_cv()
    cv_base64 = base64.b64encode(cv_bytes).decode()
    print(f"  CV size: {len(cv_bytes)} bytes")

    # Prepare request payload
    payload = {
        "cv_file": cv_base64,
        "cv_filename": "john_doe_cv.pdf",
        "position_framework": {
            "role_title": "Senior Backend Engineer",
            "key_requirements": [
                "5+ years Python experience",
                "Microservices architecture expertise",
                "Database design and optimization",
                "REST API development",
                "Cloud infrastructure experience"
            ],
            "scoring_weights": {
                "technical_skills": 40,
                "experience": 30,
                "education": 15,
                "cultural_fit": 15
            },
            "must_have_skills": ["Python", "REST API", "Database Design"],
            "nice_to_have_skills": ["Docker", "Kubernetes", "AWS"],
            "experience_years_required": 5
        },
        "company_criteria": {
            "company_name": "ACME Corp",
            "values": ["Innovation", "Collaboration", "Ownership", "Excellence"],
            "evaluation_guidelines": "Focus on problem-solving ability, architectural thinking, and team collaboration. Value candidates who demonstrate continuous learning and technical depth.",
            "disqualifiers": ["Less than 3 years experience", "No backend development experience"],
            "preferred_backgrounds": ["Computer Science degree", "Startup experience"]
        },
        "config": {
            "llm_provider": llm_provider,
            "prompt_version": "v1",
            "analysis_depth": "detailed"
        }
    }

    print(f"Sending analysis request (Provider: {llm_provider})...")

    try:
        response = requests.post(
            f"{base_url}/api/v1/analyze",
            json=payload,
            timeout=120
        )
        response.raise_for_status()

        result = response.json()

        print(f"\n{Colors.GREEN}✓ Analysis completed successfully{Colors.END}\n")

        # Display results
        print(f"{Colors.BOLD}=== ANALYSIS RESULTS ==={Colors.END}\n")

        print(f"{Colors.BOLD}Analysis ID:{Colors.END} {result['analysis_id']}")
        print(f"{Colors.BOLD}Overall Score:{Colors.END} {result['overall_score']}/100")
        print(f"{Colors.BOLD}Recommendation:{Colors.END} {result['recommendation']}")

        # Section Scores
        print(f"\n{Colors.BOLD}Section Scores:{Colors.END}")
        for section in result['section_scores']:
            print(f"\n  {Colors.BLUE}{section['section']}{Colors.END}")
            print(f"    Score: {section['score']}/100 (Weight: {section['weight']}%)")
            print(f"    Weighted: {section['weighted_score']:.2f}")
            print(f"    Rationale: {section['rationale'][:100]}...")

        # Key Strengths
        print(f"\n{Colors.BOLD}Key Strengths:{Colors.END}")
        for i, strength in enumerate(result['key_strengths'], 1):
            print(f"  {i}. {strength}")

        # Critical Gaps
        print(f"\n{Colors.BOLD}Critical Gaps:{Colors.END}")
        if result['critical_gaps']:
            for i, gap in enumerate(result['critical_gaps'], 1):
                print(f"  {i}. {gap}")
        else:
            print("  None identified")

        # Follow-up Questions
        print(f"\n{Colors.BOLD}Follow-up Questions:{Colors.END}")
        for i, question in enumerate(result['follow_up_questions'], 1):
            print(f"  {i}. {question}")

        # Metadata
        print(f"\n{Colors.BOLD}Analysis Metadata:{Colors.END}")
        metadata = result['metadata']
        print(f"  Provider: {metadata['llm_provider']}")
        print(f"  Model: {metadata['model']}")
        print(f"  Tokens Used: {metadata.get('tokens_used', 'N/A')}")
        print(f"  Processing Time: {metadata['processing_time_ms']}ms")
        print(f"  CV Pages: {metadata.get('cv_pages', 'N/A')}")

        # Save full response to file
        output_file = "test_analysis_result.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n{Colors.GREEN}Full response saved to: {output_file}{Colors.END}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"{Colors.RED}✗ Analysis failed: {e}{Colors.END}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"  Error details: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"  Response text: {e.response.text[:500]}")
        return False
    except Exception as e:
        print(f"{Colors.RED}✗ Unexpected error: {e}{Colors.END}")
        return False


def test_analyze_multipart(base_url: str, llm_provider: str = "auto") -> bool:
    """
    Test the CV analysis endpoint (Multipart upload method)

    Args:
        base_url: Base URL of the service
        llm_provider: LLM provider to use

    Returns:
        True if successful, False otherwise
    """
    print(f"\n{Colors.BOLD}Testing CV Analysis Endpoint (Multipart Upload){Colors.END}")
    print(f"{Colors.BLUE}URL: {base_url}/api/v1/analyze-upload{Colors.END}")

    # Create sample CV
    print("Creating sample CV...")
    cv_bytes = create_sample_cv()
    print(f"  CV size: {len(cv_bytes)} bytes")

    # Prepare position framework and company criteria as JSON strings
    position_framework = {
        "role_title": "Senior Backend Engineer",
        "key_requirements": [
            "5+ years Python experience",
            "Microservices architecture expertise",
            "Database design and optimization",
            "REST API development",
            "Cloud infrastructure experience"
        ],
        "scoring_weights": {
            "technical_skills": 40,
            "experience": 30,
            "education": 15,
            "cultural_fit": 15
        },
        "must_have_skills": ["Python", "REST API", "Database Design"],
        "nice_to_have_skills": ["Docker", "Kubernetes", "AWS"],
        "experience_years_required": 5
    }

    company_criteria = {
        "company_name": "ACME Corp",
        "values": ["Innovation", "Collaboration", "Ownership", "Excellence"],
        "evaluation_guidelines": "Focus on problem-solving ability, architectural thinking, and team collaboration. Value candidates who demonstrate continuous learning and technical depth.",
        "disqualifiers": ["Less than 3 years experience", "No backend development experience"],
        "preferred_backgrounds": ["Computer Science degree", "Startup experience"]
    }

    # Prepare multipart form data
    files = {
        'cv_file': ('john_doe_cv.pdf', cv_bytes, 'application/pdf')
    }

    data = {
        'position_framework': json.dumps(position_framework),
        'company_criteria': json.dumps(company_criteria),
        'llm_provider': llm_provider,
        'prompt_version': 'v1',
        'analysis_depth': 'detailed'
    }

    print(f"Sending multipart analysis request (Provider: {llm_provider})...")

    try:
        response = requests.post(
            f"{base_url}/api/v1/analyze-upload",
            files=files,
            data=data,
            timeout=120
        )
        response.raise_for_status()

        result = response.json()

        print(f"\n{Colors.GREEN}✓ Analysis completed successfully{Colors.END}\n")

        # Display results
        print(f"{Colors.BOLD}=== ANALYSIS RESULTS ==={Colors.END}\n")

        print(f"{Colors.BOLD}Analysis ID:{Colors.END} {result['analysis_id']}")
        print(f"{Colors.BOLD}Overall Score:{Colors.END} {result['overall_score']}/100")
        print(f"{Colors.BOLD}Recommendation:{Colors.END} {result['recommendation']}")

        # Section Scores
        print(f"\n{Colors.BOLD}Section Scores:{Colors.END}")
        for section in result['section_scores']:
            print(f"\n  {Colors.BLUE}{section['section']}{Colors.END}")
            print(f"    Score: {section['score']}/100 (Weight: {section['weight']}%)")
            print(f"    Weighted: {section['weighted_score']:.2f}")
            print(f"    Rationale: {section['rationale'][:100]}...")

        # Key Strengths
        print(f"\n{Colors.BOLD}Key Strengths:{Colors.END}")
        for i, strength in enumerate(result['key_strengths'], 1):
            print(f"  {i}. {strength}")

        # Critical Gaps
        print(f"\n{Colors.BOLD}Critical Gaps:{Colors.END}")
        if result['critical_gaps']:
            for i, gap in enumerate(result['critical_gaps'], 1):
                print(f"  {i}. {gap}")
        else:
            print("  None identified")

        # Follow-up Questions
        print(f"\n{Colors.BOLD}Follow-up Questions:{Colors.END}")
        for i, question in enumerate(result['follow_up_questions'], 1):
            print(f"  {i}. {question}")

        # Metadata
        print(f"\n{Colors.BOLD}Analysis Metadata:{Colors.END}")
        metadata = result['metadata']
        print(f"  Provider: {metadata['llm_provider']}")
        print(f"  Model: {metadata['model']}")
        print(f"  Tokens Used: {metadata.get('tokens_used', 'N/A')}")
        print(f"  Processing Time: {metadata['processing_time_ms']}ms")
        print(f"  CV Pages: {metadata.get('cv_pages', 'N/A')}")

        # Save full response to file
        output_file = "test_analysis_result_multipart.json"
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"\n{Colors.GREEN}Full response saved to: {output_file}{Colors.END}")

        return True

    except requests.exceptions.RequestException as e:
        print(f"{Colors.RED}✗ Analysis failed: {e}{Colors.END}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                print(f"  Error details: {json.dumps(error_detail, indent=2)}")
            except:
                print(f"  Response text: {e.response.text[:500]}")
        return False
    except Exception as e:
        print(f"{Colors.RED}✗ Unexpected error: {e}{Colors.END}")
        return False


def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(
        description='Test CV Analysis Service',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_service.py
  python test_service.py --url http://localhost:8000
  python test_service.py --provider anthropic
  python test_service.py --method multipart
  python test_service.py --url http://localhost:8000 --provider openai --method base64
  python test_service.py --method both
        """
    )
    parser.add_argument(
        '--url',
        default='http://localhost:8000',
        help='Base URL of the service (default: http://localhost:8000)'
    )
    parser.add_argument(
        '--provider',
        default='auto',
        choices=['auto', 'openai', 'anthropic', 'gemini'],
        help='LLM provider to use (default: auto)'
    )
    parser.add_argument(
        '--method',
        default='multipart',
        choices=['base64', 'multipart', 'both'],
        help='Upload method to test (default: multipart, recommended for efficiency)'
    )
    parser.add_argument(
        '--health-only',
        action='store_true',
        help='Only run health check, skip analysis'
    )

    args = parser.parse_args()

    print(f"{Colors.BOLD}{Colors.BLUE}")
    print("=" * 60)
    print("CV Analysis Service - Test Script")
    print("=" * 60)
    print(f"{Colors.END}")

    print(f"Service URL: {args.url}")
    print(f"LLM Provider: {args.provider}")
    print(f"Upload Method: {args.method}")

    # Test health endpoint
    health_ok = test_health(args.url)

    if not health_ok:
        print(f"\n{Colors.RED}Service is not healthy. Please ensure:")
        print("  1. The service is running")
        print("  2. The service is accessible at the specified URL")
        print(f"  3. At least one LLM provider is configured{Colors.END}")
        sys.exit(1)

    if args.health_only:
        print(f"\n{Colors.GREEN}Health check only - skipping analysis test{Colors.END}")
        sys.exit(0)

    # Test analysis endpoint(s)
    base64_ok = True
    multipart_ok = True

    if args.method in ['base64', 'both']:
        base64_ok = test_analyze(args.url, args.provider)

    if args.method in ['multipart', 'both']:
        multipart_ok = test_analyze_multipart(args.url, args.provider)

    # Summary
    print(f"\n{Colors.BOLD}{'=' * 60}{Colors.END}")
    print(f"{Colors.BOLD}Test Summary{Colors.END}")
    print(f"{'=' * 60}")

    health_status = f"{Colors.GREEN}PASS{Colors.END}" if health_ok else f"{Colors.RED}FAIL{Colors.END}"
    print(f"Health Check: {health_status}")

    if args.method in ['base64', 'both']:
        base64_status = f"{Colors.GREEN}PASS{Colors.END}" if base64_ok else f"{Colors.RED}FAIL{Colors.END}"
        print(f"CV Analysis (Base64): {base64_status}")

    if args.method in ['multipart', 'both']:
        multipart_status = f"{Colors.GREEN}PASS{Colors.END}" if multipart_ok else f"{Colors.RED}FAIL{Colors.END}"
        print(f"CV Analysis (Multipart): {multipart_status}")

    all_ok = health_ok and base64_ok and multipart_ok
    if all_ok:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✓ All tests passed!{Colors.END}")
        sys.exit(0)
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}✗ Some tests failed{Colors.END}")
        sys.exit(1)


if __name__ == "__main__":
    main()
