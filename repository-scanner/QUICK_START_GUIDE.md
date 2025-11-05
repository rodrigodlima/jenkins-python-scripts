# 🚀 Quick Start Guide - Jenkins Complete Scanner v2.0

## ⚡ Quick Setup

### Step 1: Install Dependencies
```bash
pip install requests
```

### Step 2: Run Complete Scan
```bash
# NO Git repositories required! Works immediately.
python complete_scanner.py \
    --jenkins-url https://jenkins.company.com \
    --username YOUR_USERNAME \
    --token YOUR_API_TOKEN \
    --parameters ECR_PATH AWS_REGION
```

**Note:** Git repositories are **optional**. See "Git Repositories" section below.

### Step 3: View Results
```bash
# Open the interactive HTML report
firefox jenkins_scan_results/*/reports/report.html

# Or check the summary
cat jenkins_scan_results/*/reports/summary.txt
```

---

## 📊 What You'll Get

```
jenkins_scan_results/20241104_143022/
├── configs/              # All job configurations (*.xml)
├── reports/
│   ├── report.html      # ⭐ Interactive visual report
│   └── summary.txt      # Text summary
└── exports/
    ├── jobs_parameters.csv   # For Excel/Google Sheets
    └── complete_scan.json    # Complete data (JSON)
```

---

## 🎯 Main Features

### 1. Export Jenkins Configurations
- Downloads `config.xml` of **ALL** jobs
- Organizes in structured directories
- Extracts metadata automatically

### 2. Scan All Jobs
- Searches for parameters in all configurations
- Identifies where parameters are:
  - **Defined** (as job parameter)
  - **Used** (in script/Jenkinsfile)
  - **Hardcoded** (used but not defined)

### 3. Share Results
- **HTML Report**: Visual, interactive, searchable
- **CSV Export**: For Excel/Google Sheets analysis
- **JSON Export**: For automation/integration
- **Email**: Send directly to team
- **ZIP**: Shareable package

---

## 📧 Sharing Results

### Option 1: Create ZIP
```bash
python share_results.py \
    --scan-dir jenkins_scan_results/20241104_143022 \
    --create-zip
```

### Option 2: Send via Email
```bash
python share_results.py \
    --scan-dir jenkins_scan_results/20241104_143022 \
    --email \
    --smtp-server smtp.gmail.com \
    --smtp-port 587 \
    --sender jenkins@company.com \
    --sender-password "your_password" \
    --recipients team@company.com manager@company.com
```

### Option 3: Temporary HTTP Server
```bash
cd jenkins_scan_results/20241104_143022/reports
python3 -m http.server 8000
# Access: http://localhost:8000/report.html
# Share URL with team
```

---

## 🔑 Getting Jenkins API Token

1. Log in to Jenkins
2. Click on your username (top right)
3. Click **"Configure"**
4. Scroll to **"API Token"** section
5. Click **"Add new Token"**
6. Give it a name (e.g., "scanner")
7. Click **"Generate"**
8. **Copy the token** (won't be shown again!)

---

## 📁 Git Repositories (Optional)

### Do I Need Them?

**Most cases: NO!** The scanner works perfectly without Git repos.

**Clone repos only if:**
- You have many "Pipeline from SCM" jobs
- You want to analyze Jenkinsfiles from Git
- You need complete parameter analysis

### Without Git Repos (Default - Recommended)
```bash
python complete_scanner.py \
    --jenkins-url https://jenkins.company.com \
    --username admin \
    --token abc123 \
    --parameters ECR_PATH
```

**What you get:**
- ✅ All job configs exported
- ✅ Full analysis of inline Pipeline Scripts
- ✅ Git URLs for Pipeline from SCM jobs
- ⚠️ Can't read Jenkinsfiles from SCM

### With Git Repos (Optional - Enhanced)
```bash
# 1. Clone repos first
mkdir ~/repos
git clone https://git.company.com/project1.git ~/repos/project1

# 2. Run with Git support
python complete_scanner.py \
    --jenkins-url https://jenkins.company.com \
    --username admin \
    --token abc123 \
    --git-repos-path ~/repos \
    --parameters ECR_PATH
```

**Additional benefits:**
- ✅ Reads and analyzes Jenkinsfiles
- ✅ Complete parameter analysis
- ✅ Best for thorough audits

**📖 For complete guide, see:** `GIT_REPOS_GUIDE.md`

---

## 📝 Configuration File (Optional)

### Option 1: Config File

If you don't want to pass credentials every time:

```bash
# 1. Copy example config
cp config.ini.example config.ini

# 2. Edit with your credentials
nano config.ini
```

```ini
[jenkins]
url = https://jenkins.company.com
username = your_username
token = your_api_token

[search]
default_parameter = ECR_PATH
```

```bash
# 3. Run without arguments
python complete_scanner.py
```

### Option 2: Environment Variables (Recommended for Scripts)

Export variables in your terminal:

```bash
# Set environment variables
export JENKINS_URL="https://jenkins.company.com"
export JENKINS_USER="your_username"
export JENKINS_TOKEN="your_api_token"

# Use in commands
python complete_scanner.py \
    --jenkins-url $JENKINS_URL \
    --username $JENKINS_USER \
    --token $JENKINS_TOKEN \
    --parameters ECR_PATH
```

**For permanent setup (Linux/Mac):**
```bash
# Add to ~/.bashrc or ~/.zshrc
echo 'export JENKINS_USER="your_username"' >> ~/.bashrc
echo 'export JENKINS_TOKEN="your_token"' >> ~/.bashrc
source ~/.bashrc
```

**See ENVIRONMENT_VARIABLES.md for complete guide including:**
- Secure .env file method
- Docker integration
- CI/CD integration (GitHub Actions, GitLab CI, Jenkins)
- Secrets management (AWS, Vault)

---

## 🎓 Use Case Examples

### Weekly Audit
```bash
#!/bin/bash
# weekly_audit.sh

python complete_scanner.py \
    --jenkins-url https://jenkins.company.com \
    --username $JENKINS_USER \
    --token $JENKINS_TOKEN \
    --parameters ECR_PATH AWS_REGION DOCKER_REGISTRY

# Email results
SCAN_DIR=$(ls -td jenkins_scan_results/* | head -1)
python share_results.py \
    --scan-dir $SCAN_DIR \
    --email \
    --smtp-server smtp.company.com \
    --sender audit@company.com \
    --recipients team@company.com
```

Schedule with cron:
```bash
crontab -e
# Add: 0 8 * * 1 /path/to/weekly_audit.sh  # Every Monday at 8am
```

---

### Parameter Migration
```bash
# Before migration
python complete_scanner.py \
    --jenkins-url https://jenkins.company.com \
    --username admin \
    --token abc123 \
    --parameters OLD_REGISTRY_URL \
    --output-dir scan_before

# After migration
python complete_scanner.py \
    --jenkins-url https://jenkins.company.com \
    --username admin \
    --token abc123 \
    --parameters NEW_REGISTRY_URL \
    --output-dir scan_after

# Compare results
diff scan_before/*/reports/summary.txt scan_after/*/reports/summary.txt
```

---

### Compliance Audit
```bash
# Scan for sensitive parameters
python complete_scanner.py \
    --jenkins-url https://jenkins.company.com \
    --username admin \
    --token abc123 \
    --parameters \
        AWS_ACCESS_KEY \
        AWS_SECRET_KEY \
        DB_PASSWORD \
        API_SECRET \
        PRIVATE_KEY

# Create ZIP for security team
python share_results.py \
    --scan-dir jenkins_scan_results/* \
    --create-zip
```

---

## 🔍 Available Scripts

| Script | Purpose | When to Use |
|--------|---------|-------------|
| **complete_scanner.py** ⭐ | Does everything (export + scan + reports) | **Most common use** |
| jenkins_config_exporter.py | Only exports configurations | Backup only |
| enhanced_jenkins_scanner.py | Advanced scan with Git support | With local Git repos |
| share_results.py | Shares results | After scanning |
| unified_scanner.py | Scanner + Git + Cross-analysis | Deep analysis |

---

## 🐛 Troubleshooting

### Connection Refused
```bash
# Check URL
curl -I https://jenkins.company.com

# Check VPN/firewall
ping jenkins.company.com
```

### 401 Unauthorized
- Token expired → Generate new token
- Wrong username → Verify credentials
- Insufficient permissions → Contact Jenkins admin

### Timeout
- Jenkins overloaded → Run during off-peak hours
- Network issues → Check connection
- Too many jobs → Increase timeout in code

### No Results Found
- Parameter name case-sensitive → Check exact name
- Parameter only in Jenkinsfile → Use Git repos path
- Parameter renamed → Search for old name

---

## 💡 Tips & Tricks

### Search Multiple Parameters at Once
```bash
python complete_scanner.py \
    --jenkins-url ... \
    --parameters \
        ECR_PATH \
        AWS_REGION \
        DOCKER_REGISTRY \
        IMAGE_TAG \
        KUBERNETES_NAMESPACE
```

### Custom Output Directory
```bash
python complete_scanner.py \
    --jenkins-url ... \
    --output-dir /backup/jenkins-audits
```

### Filter Results with jq
```bash
# Jobs using parameter but not defining it
cat jenkins_scan_results/*/exports/complete_scan.json | \
    jq '.jobs[] | select(.parameters_found.ECR_PATH.used_in_script == true and .parameters_found.ECR_PATH.defined_as_parameter == false) | .job_name'

# Count jobs by pipeline type
cat jenkins_scan_results/*/exports/complete_scan.json | \
    jq '.jobs[].metadata.pipeline_type' | sort | uniq -c
```

### Analyze in Python
```python
import json
import pandas as pd

# Load results
with open('jenkins_scan_results/.../exports/complete_scan.json') as f:
    data = json.load(f)

# Convert to DataFrame
jobs = pd.DataFrame(data['jobs'])

# Find hardcoded parameters
hardcoded = jobs[
    jobs['parameters_found'].apply(
        lambda x: x.get('ECR_PATH', {}).get('used_in_script') and 
                  not x.get('ECR_PATH', {}).get('defined_as_parameter')
    )
]

print(f"Jobs with hardcoded ECR_PATH: {len(hardcoded)}")
print(hardcoded[['job_name', 'job_url']])
```

---

## 📚 More Documentation

- **README.md** - Complete overview
- **README_FIRST.txt** - Quick reference card
- **config.ini.example** - Configuration template

---

## ✅ Quick Checklist

- [ ] Install dependencies: `pip install requests`
- [ ] Generate Jenkins API token
- [ ] Run scan: `python complete_scanner.py ...`
- [ ] Open HTML report in browser
- [ ] Analyze results
- [ ] Share with team (ZIP or email)
- [ ] (Optional) Schedule weekly scan

---

## 🚀 Get Started Now!

```bash
python complete_scanner.py \
    --jenkins-url https://jenkins.company.com \
    --username YOUR_USERNAME \
    --token YOUR_TOKEN \
    --parameters ECR_PATH

firefox jenkins_scan_results/*/reports/report.html
```

**That's it! Happy scanning! 🎉**
