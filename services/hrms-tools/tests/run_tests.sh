#!/bin/bash
# Convenience script to run CV Analysis Service tests

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Default values
SERVICE_URL="${SERVICE_URL:-http://localhost:8000}"
PROVIDER="${PROVIDER:-auto}"

echo -e "${BLUE}================================${NC}"
echo -e "${BLUE}CV Analysis Service Test Runner${NC}"
echo -e "${BLUE}================================${NC}"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

# Check if dependencies are installed
echo -e "${YELLOW}Checking dependencies...${NC}"
if ! python3 -c "import requests" 2>/dev/null; then
    echo -e "${YELLOW}Installing test dependencies...${NC}"
    pip install -r requirements.txt
fi

# Check if service is running
echo -e "${YELLOW}Checking if service is running...${NC}"
if curl -s -f "${SERVICE_URL}/api/v1/health" > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Service is running at ${SERVICE_URL}${NC}"
else
    echo -e "${RED}✗ Service is not reachable at ${SERVICE_URL}${NC}"
    echo ""
    echo "Please start the service first:"
    echo "  docker-compose up -d"
    echo "  OR"
    echo "  python -m app.main"
    echo ""
    echo "Or specify a different URL:"
    echo "  SERVICE_URL=http://your-server:8000 ./run_tests.sh"
    exit 1
fi

echo ""

# Run tests
echo -e "${BLUE}Running tests...${NC}"
echo ""

python3 test_service.py --url "${SERVICE_URL}" --provider "${PROVIDER}"

exit_code=$?

echo ""
if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}================================${NC}"
    echo -e "${GREEN}All tests passed successfully!${NC}"
    echo -e "${GREEN}================================${NC}"
else
    echo -e "${RED}================================${NC}"
    echo -e "${RED}Some tests failed${NC}"
    echo -e "${RED}================================${NC}"
fi

exit $exit_code
