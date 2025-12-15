#!/bin/bash

# Test Execution Script for The Hive Platform
# Runs all tests and generates coverage reports

set -e

echo "=========================================="
echo "The Hive Platform - Test Execution"
echo "=========================================="
echo ""

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}Test Environment:${NC}"
echo "  - Database: SQLite (in-memory)"
echo "  - Framework: Django TestCase"
echo "  - Coverage Tool: Coverage.py"
echo ""

echo -e "${YELLOW}Step 1: Running All Tests${NC}"
echo "----------------------------------------"
python3 manage.py test the_hive.tests --verbosity=2 2>&1 | tee test_results.txt

TEST_EXIT_CODE=${PIPESTATUS[0]}

if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed${NC}"
else
    echo -e "${RED}✗ Some tests failed${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}Step 2: Generating Coverage Report${NC}"
echo "----------------------------------------"

coverage run --source='the_hive' manage.py test the_hive.tests --verbosity=0
coverage report -m > coverage_report.txt
coverage html -d htmlcov

echo -e "${GREEN}✓ Coverage report generated${NC}"
echo ""

echo -e "${YELLOW}Coverage Summary:${NC}"
coverage report | tail -1

echo ""
echo -e "${YELLOW}Step 3: Test Summary${NC}"
echo "----------------------------------------"

TOTAL_TESTS=$(grep -oP '\d+ test' test_results.txt | grep -oP '\d+' | head -1 || echo "0")
PASSED_TESTS=$(grep -c "OK" test_results.txt 2>/dev/null || echo "0")
FAILED_TESTS=$(grep -c "FAILED" test_results.txt 2>/dev/null || echo "0")

echo "Total tests: $TOTAL_TESTS"
echo "Tests passed: $PASSED_TESTS"
echo "Tests failed: $FAILED_TESTS"

echo ""
echo "=========================================="
echo "Test execution completed!"
echo "=========================================="
echo ""
echo "Reports generated:"
echo "  - test_results.txt (detailed test output)"
echo "  - coverage_report.txt (coverage report)"
echo "  - htmlcov/ (HTML coverage report)"
echo ""
