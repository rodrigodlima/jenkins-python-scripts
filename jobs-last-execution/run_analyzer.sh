#!/bin/bash
set -e

echo "Jenkins Inactive Jobs Analyzer"
echo "=================================="
echo ""

if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

if ! python3 -c "import requests" 2>/dev/null; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
    echo "Dependencies installed"
    echo ""
fi

if [ -f .env ]; then
    echo "Loading configuration from .env file"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo "Warning: .env file not found"
    echo "Tip: Copy .env.example to .env and configure your credentials"
    echo ""
fi

if [ -z "$JENKINS_URL" ] || [ -z "$JENKINS_USER" ] || [ -z "$JENKINS_TOKEN" ]; then
    echo "Error: Environment variables not configured"
    echo ""
    echo "Configure the following environment variables:"
    echo "  - JENKINS_URL"
    echo "  - JENKINS_USER"
    echo "  - JENKINS_TOKEN"
    echo ""
    echo "Options:"
    echo "  1. Create .env file (recommended)"
    echo "  2. Export manually: export JENKINS_URL=..."
    echo "  3. Pass parameters: python3 jenkins_inactive_jobs_analyzer.py --help"
    exit 1
fi

echo "Starting analysis..."
echo ""
python3 jenkins_inactive_jobs_analyzer.py "$@"

LATEST_REPORT=$(ls -t jenkins_reports/jobs_report_*.csv 2>/dev/null | head -n1)

if [ ! -z "$LATEST_REPORT" ]; then
    echo ""
    echo "CSV report generated: $LATEST_REPORT"
    echo ""
    read -p "Open CSV report? (y/N): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if command -v open &> /dev/null; then
            open "$LATEST_REPORT"
        elif command -v xdg-open &> /dev/null; then
            xdg-open "$LATEST_REPORT"
        else
            echo "Warning: Could not open CSV automatically"
            echo "   Open manually: $LATEST_REPORT"
        fi
    fi
fi

echo ""
echo "Analysis completed!"
