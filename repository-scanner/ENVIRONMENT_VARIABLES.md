# 🔐 Environment Variables Setup Guide

## Overview

Instead of passing credentials directly in the command line, you can use environment variables for better security and convenience.

---

## ⚡ Quick Setup

### Option 1: Temporary (Current Session Only)

```bash
# Export variables in your current terminal session
export JENKINS_URL="https://jenkins.company.com"
export JENKINS_USER="your_username"
export JENKINS_TOKEN="your_api_token_here"

# Run scanner using environment variables
python complete_scanner.py \
    --jenkins-url $JENKINS_URL \
    --username $JENKINS_USER \
    --token $JENKINS_TOKEN \
    --parameters ECR_PATH
```

**Note:** These variables will be lost when you close the terminal.

---

### Option 2: Permanent (All Sessions)

#### For Linux/Mac (bash/zsh):

```bash
# 1. Edit your shell profile
nano ~/.bashrc     # For bash
# OR
nano ~/.zshrc      # For zsh

# 2. Add these lines at the end:
export JENKINS_URL="https://jenkins.company.com"
export JENKINS_USER="your_username"  
export JENKINS_TOKEN="your_api_token_here"

# 3. Save and reload
source ~/.bashrc   # For bash
# OR
source ~/.zshrc    # For zsh

# 4. Verify
echo $JENKINS_USER
```

#### For Windows (PowerShell):

```powershell
# Temporary (current session):
$env:JENKINS_URL = "https://jenkins.company.com"
$env:JENKINS_USER = "your_username"
$env:JENKINS_TOKEN = "your_api_token_here"

# Permanent (all sessions):
[System.Environment]::SetEnvironmentVariable('JENKINS_URL', 'https://jenkins.company.com', 'User')
[System.Environment]::SetEnvironmentVariable('JENKINS_USER', 'your_username', 'User')
[System.Environment]::SetEnvironmentVariable('JENKINS_TOKEN', 'your_api_token_here', 'User')

# Verify
echo $env:JENKINS_USER
```

---

## 🔒 Secure .env File Method (Recommended)

### Step 1: Create .env file

```bash
# Create .env file in your project directory
cat > .env << 'EOF'
JENKINS_URL=https://jenkins.company.com
JENKINS_USER=your_username
JENKINS_TOKEN=your_api_token_here
EOF

# Set secure permissions (Linux/Mac only)
chmod 600 .env
```

### Step 2: Load .env file

**Option A: Manual loading**
```bash
# Load variables from .env
source .env

# Or for multiple variables:
export $(cat .env | xargs)

# Run scanner
python complete_scanner.py \
    --jenkins-url $JENKINS_URL \
    --username $JENKINS_USER \
    --token $JENKINS_TOKEN \
    --parameters ECR_PATH
```

**Option B: Python dotenv (install required)**
```bash
pip install python-dotenv
```

Create a wrapper script:
```python
# run_scanner.py
from dotenv import load_dotenv
import os
import subprocess

# Load .env file
load_dotenv()

# Get variables
jenkins_url = os.getenv('JENKINS_URL')
jenkins_user = os.getenv('JENKINS_USER')
jenkins_token = os.getenv('JENKINS_TOKEN')

# Run scanner
cmd = [
    'python', 'complete_scanner.py',
    '--jenkins-url', jenkins_url,
    '--username', jenkins_user,
    '--token', jenkins_token,
    '--parameters', 'ECR_PATH', 'AWS_REGION'
]

subprocess.run(cmd)
```

---

## 📝 Complete Examples

### Example 1: Weekly Audit Script with Environment Variables

```bash
#!/bin/bash
# weekly_audit.sh

# Check if variables are set
if [ -z "$JENKINS_USER" ] || [ -z "$JENKINS_TOKEN" ]; then
    echo "Error: Environment variables not set!"
    echo "Please run: export JENKINS_USER=... and JENKINS_TOKEN=..."
    exit 1
fi

# Run scan
python complete_scanner.py \
    --jenkins-url ${JENKINS_URL:-"https://jenkins.company.com"} \
    --username $JENKINS_USER \
    --token $JENKINS_TOKEN \
    --parameters ECR_PATH AWS_REGION DOCKER_REGISTRY

# Share results
SCAN_DIR=$(ls -td jenkins_scan_results/* | head -1)
python share_results.py \
    --scan-dir $SCAN_DIR \
    --create-zip

echo "✅ Audit complete! Results in: $SCAN_DIR"
```

Make it executable:
```bash
chmod +x weekly_audit.sh
```

---

### Example 2: Config File with Environment Variables

```bash
# setup_jenkins_scan.sh

# Load from config file
if [ -f ~/.jenkins_scanner_config ]; then
    source ~/.jenkins_scanner_config
else
    echo "Creating config file..."
    cat > ~/.jenkins_scanner_config << EOF
export JENKINS_URL="https://jenkins.company.com"
export JENKINS_USER="your_username"
export JENKINS_TOKEN="your_token_here"
EOF
    chmod 600 ~/.jenkins_scanner_config
    echo "Config created at ~/.jenkins_scanner_config"
    echo "Please edit it with your credentials"
    exit 1
fi

# Run scanner
python complete_scanner.py \
    --jenkins-url $JENKINS_URL \
    --username $JENKINS_USER \
    --token $JENKINS_TOKEN \
    "$@"  # Pass any additional arguments
```

Usage:
```bash
./setup_jenkins_scan.sh --parameters ECR_PATH AWS_REGION
```

---

### Example 3: Docker Container with Environment Variables

```dockerfile
# Dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . /app
RUN pip install -r requirements.txt

# Environment variables (override at runtime)
ENV JENKINS_URL=""
ENV JENKINS_USER=""
ENV JENKINS_TOKEN=""

ENTRYPOINT ["python", "complete_scanner.py"]
CMD ["--jenkins-url", "$JENKINS_URL", "--username", "$JENKINS_USER", "--token", "$JENKINS_TOKEN"]
```

Build and run:
```bash
# Build
docker build -t jenkins-scanner .

# Run with environment variables
docker run -e JENKINS_URL="https://jenkins.company.com" \
           -e JENKINS_USER="admin" \
           -e JENKINS_TOKEN="abc123" \
           jenkins-scanner \
           --parameters ECR_PATH

# Or use .env file
docker run --env-file .env jenkins-scanner --parameters ECR_PATH
```

---

## 🔐 Security Best Practices

### 1. Never Commit Credentials
```bash
# Add to .gitignore
echo ".env" >> .gitignore
echo "*.env" >> .gitignore
echo ".jenkins_scanner_config" >> .gitignore
echo "config.ini" >> .gitignore
```

### 2. Use Secrets Management (Production)

**AWS Secrets Manager:**
```bash
# Store token
aws secretsmanager create-secret \
    --name jenkins/api-token \
    --secret-string "your_token_here"

# Retrieve and use
export JENKINS_TOKEN=$(aws secretsmanager get-secret-value \
    --secret-id jenkins/api-token \
    --query SecretString \
    --output text)

python complete_scanner.py \
    --jenkins-url https://jenkins.company.com \
    --username admin \
    --token $JENKINS_TOKEN \
    --parameters ECR_PATH
```

**HashiCorp Vault:**
```bash
# Read secret
export JENKINS_TOKEN=$(vault kv get -field=token secret/jenkins)

python complete_scanner.py \
    --jenkins-url https://jenkins.company.com \
    --username admin \
    --token $JENKINS_TOKEN \
    --parameters ECR_PATH
```

### 3. Rotate Tokens Regularly
```bash
# Revoke old token in Jenkins UI
# Generate new token
# Update environment variable
export JENKINS_TOKEN="new_token_here"
```

---

## 🚀 Integration with CI/CD

### GitHub Actions

```yaml
# .github/workflows/jenkins-audit.yml
name: Jenkins Audit

on:
  schedule:
    - cron: '0 8 * * 1'  # Every Monday at 8am
  workflow_dispatch:

jobs:
  audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run Jenkins Scan
        env:
          JENKINS_URL: ${{ secrets.JENKINS_URL }}
          JENKINS_USER: ${{ secrets.JENKINS_USER }}
          JENKINS_TOKEN: ${{ secrets.JENKINS_TOKEN }}
        run: |
          python complete_scanner.py \
            --jenkins-url $JENKINS_URL \
            --username $JENKINS_USER \
            --token $JENKINS_TOKEN \
            --parameters ECR_PATH AWS_REGION
      
      - name: Upload Report
        uses: actions/upload-artifact@v3
        with:
          name: jenkins-scan-report
          path: jenkins_scan_results/
```

**Setup GitHub Secrets:**
1. Go to repository Settings → Secrets and variables → Actions
2. Add secrets:
   - `JENKINS_URL`
   - `JENKINS_USER`
   - `JENKINS_TOKEN`

---

### GitLab CI

```yaml
# .gitlab-ci.yml
jenkins-audit:
  stage: audit
  image: python:3.9-slim
  
  before_script:
    - pip install -r requirements.txt
  
  script:
    - |
      python complete_scanner.py \
        --jenkins-url $JENKINS_URL \
        --username $JENKINS_USER \
        --token $JENKINS_TOKEN \
        --parameters ECR_PATH AWS_REGION
  
  artifacts:
    paths:
      - jenkins_scan_results/
    expire_in: 30 days
  
  only:
    - schedules
```

**Setup GitLab Variables:**
1. Go to Settings → CI/CD → Variables
2. Add variables (mark as "Protected" and "Masked"):
   - `JENKINS_URL`
   - `JENKINS_USER`
   - `JENKINS_TOKEN`

---

### Jenkins Pipeline (Scanning Jenkins from Jenkins 🤯)

```groovy
// Jenkinsfile
pipeline {
    agent any
    
    triggers {
        cron('0 8 * * 1')  // Every Monday at 8am
    }
    
    environment {
        JENKINS_URL = "${JENKINS_URL}"
        JENKINS_USER = credentials('jenkins-api-user')
        JENKINS_TOKEN = credentials('jenkins-api-token')
    }
    
    stages {
        stage('Setup') {
            steps {
                sh 'pip install -r requirements.txt'
            }
        }
        
        stage('Scan Jenkins') {
            steps {
                sh '''
                    python complete_scanner.py \
                        --jenkins-url $JENKINS_URL \
                        --username $JENKINS_USER \
                        --token $JENKINS_TOKEN \
                        --parameters ECR_PATH AWS_REGION
                '''
            }
        }
        
        stage('Archive Results') {
            steps {
                archiveArtifacts artifacts: 'jenkins_scan_results/**/*'
                publishHTML([
                    reportName: 'Jenkins Scan Report',
                    reportDir: 'jenkins_scan_results',
                    reportFiles: '**/reports/report.html'
                ])
            }
        }
    }
}
```

---

## 🛠️ Troubleshooting

### Variables Not Found
```bash
# Check if variables are set
echo $JENKINS_USER
echo $JENKINS_TOKEN

# If empty, they're not set
# Set them again or check your profile file
```

### Permission Denied
```bash
# Make sure .env file has correct permissions
chmod 600 .env

# Make sure scripts are executable
chmod +x *.sh
```

### Variables Not Persisting
```bash
# Make sure you edited the correct profile file
# For bash:
nano ~/.bashrc

# For zsh:
nano ~/.zshrc

# After editing, reload:
source ~/.bashrc  # or ~/.zshrc

# Verify it persists in a new terminal
```

---

## 📋 Quick Reference

### Export Environment Variables
```bash
# Temporary
export JENKINS_USER="username"
export JENKINS_TOKEN="token"

# Permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export JENKINS_USER="username"' >> ~/.bashrc
echo 'export JENKINS_TOKEN="token"' >> ~/.bashrc
source ~/.bashrc
```

### Use Variables in Commands
```bash
python complete_scanner.py \
    --jenkins-url $JENKINS_URL \
    --username $JENKINS_USER \
    --token $JENKINS_TOKEN \
    --parameters ECR_PATH
```

### Check Variables
```bash
# Show variable value
echo $JENKINS_USER

# List all environment variables
env | grep JENKINS
```

### Unset Variables
```bash
# Remove from current session
unset JENKINS_USER
unset JENKINS_TOKEN

# Remove from profile
nano ~/.bashrc  # Delete the export lines
source ~/.bashrc
```

---

## ✅ Recommended Setup

**For Development:**
```bash
# Use .env file
cat > .env << EOF
JENKINS_URL=https://jenkins.company.com
JENKINS_USER=your_username
JENKINS_TOKEN=your_token
EOF

# Load before running
export $(cat .env | xargs)
```

**For Production/CI:**
- Use secrets management system
- Never commit credentials
- Use masked/protected variables in CI platforms

---

**Now you can securely use environment variables with the scanner! 🔐**
