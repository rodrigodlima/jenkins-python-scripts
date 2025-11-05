# Jenkins Complete Scanner v2.0 🚀

## 🎯 Export → Scan → Share

Complete suite to audit, export and share Jenkins analyses.

### ✨ What's New in v2.0

- ✅ **Export Jenkins Configurations** - Exports all job configs
- ✅ **Scan All Jobs** - Search parameters in all configurations  
- ✅ **Share Results** - Shareable reports (HTML, CSV, JSON, Email)

---

## 🚀 Quick Start

### One command does EVERYTHING:

```bash
# NO Git repositories needed! Works out of the box.
python complete_scanner.py \
    --jenkins-url https://jenkins.company.com \
    --username admin \
    --token abc123 \
    --parameters ECR_PATH AWS_REGION
```

**Result:**
```
jenkins_scan_results/20241104_143022/
├── configs/           # Config.xml of ALL jobs
├── reports/
│   ├── report.html   # 🌐 Interactive report (OPEN THIS!)
│   └── summary.txt   # Text summary
└── exports/
    ├── jobs_parameters.csv  # For Excel/Sheets
    └── complete_scan.json   # Complete data
```

---

## 📦 What's Included

### Main Scripts

| Script | Description | When to Use |
|--------|-------------|-------------|
| **`complete_scanner.py`** ⭐ | Does EVERYTHING (export + scan + reports) | **Recommended for most cases** |
| `jenkins_config_exporter.py` | Only exports configurations | Config backup |
| `enhanced_jenkins_scanner.py` | Advanced scan with Git | Detailed analysis |
| `share_results.py` | Shares results | After scanning |
| `unified_scanner.py` | Scanner + Git + Cross-analysis | Deep analysis |

### Documentation

| File | Content |
|------|---------|
| **`README_FIRST.txt`** ⭐ | Quick start instructions |
| `WHATS_NEW.md` | New features in v2.0 |
| `GIT_REPOS_GUIDE.md` | When do you need Git repos? |
| `ENVIRONMENT_VARIABLES.md` | Complete env vars setup |
| `QUICK_START_GUIDE.md` | Detailed tutorial |

---

## 📁 Do I Need Git Repositories?

### Short Answer: **NO!** (But they help for certain job types)

**Without Git repos (default):**
```bash
python complete_scanner.py \
    --jenkins-url https://jenkins.company.com \
    --username admin \
    --token abc123 \
    --parameters ECR_PATH
```
- ✅ Works perfectly for most cases
- ✅ Full analysis of "Pipeline Script" (inline) jobs
- ⚠️ Limited analysis of "Pipeline from SCM" jobs

**With Git repos (optional):**
```bash
# Clone repos first
mkdir ~/repos
git clone https://git.company.com/project1.git ~/repos/project1

# Run with Git support
python complete_scanner.py \
    --jenkins-url https://jenkins.company.com \
    --username admin \
    --token abc123 \
    --git-repos-path ~/repos \
    --parameters ECR_PATH
```
- ✅ Complete analysis of ALL job types
- ✅ Reads and analyzes Jenkinsfiles from Git
- ✅ Best for thorough audits

**📖 See `GIT_REPOS_GUIDE.md` for:**
- When to clone repos
- How to clone efficiently
- Performance impact
- Decision matrix

---

## 🎯 Main Use Cases

### 1. Complete Audit (most common)

```bash
# Export + Scan + Reports in one command
python complete_scanner.py \
    --jenkins-url https://jenkins.company.com \
    --username admin \
    --token abc123 \
    --parameters ECR_PATH AWS_REGION DOCKER_REGISTRY
```

**You get:**
- ✅ All configurations exported
- ✅ Analysis of which jobs use the parameters
- ✅ Beautiful and interactive HTML report
- ✅ CSV for Excel
- ✅ JSON for automation

---

### 2. Share with Team

```bash
# Generate shareable ZIP
python share_results.py \
    --scan-dir jenkins_scan_results/20241104_143022 \
    --create-zip

# Or send via email
python share_results.py \
    --scan-dir jenkins_scan_results/20241104_143022 \
    --email \
    --smtp-server smtp.gmail.com \
    --sender you@company.com \
    --recipients team@company.com manager@company.com
```

---

### 3. Export Configurations Only (Backup)

```bash
python jenkins_config_exporter.py \
    --jenkins-url https://jenkins.company.com \
    --username admin \
    --token abc123 \
    --export-dir /backup/jenkins
```

---

## 📊 Generated Reports

### 1. Interactive HTML 🌐

Visual report with:
- Summary statistics
- Real-time search
- Tables per parameter
- Direct links to jobs
- Responsive design

**Open:** `reports/report.html`

---

### 2. CSV Export 📊

For analysis in Excel/Google Sheets:
- Lists all jobs
- Columns for each parameter
- Indicates if defined/used
- Counts occurrences

**File:** `exports/jobs_parameters.csv`

---

### 3. Complete JSON 🔧

Structured data for:
- Automation
- Programmatic processing
- Integration with other tools

**File:** `exports/complete_scan.json`

---

## 🔧 Installation

```bash
# 1. Extract the ZIP
unzip jenkins-complete-scanner-v2.0-EN.zip

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure credentials (choose one method)

# Method A: Config file (optional)
cp config.ini.example config.ini
nano config.ini

# Method B: Environment variables (recommended for scripts)
export JENKINS_USER="your_username"
export JENKINS_TOKEN="your_api_token"

# 4. Run
python complete_scanner.py --help
```

**📖 For detailed environment variables setup, see:** `ENVIRONMENT_VARIABLES.md`

---

## 🎓 Quick Tutorials

### Tutorial 1: First Audit (5 minutes)

```bash
# 1. Generate token in Jenkins
# Jenkins > Your User > Configure > API Token

# 2. Run the scan
python complete_scanner.py \
    --jenkins-url https://jenkins.company.com \
    --username your_username \
    --token your_token \
    --parameters ECR_PATH

# 3. Open the report
firefox jenkins_scan_results/*/reports/report.html

# Done! ✅
```

---

### Tutorial 2: Share with Manager (3 minutes)

```bash
# 1. After running the scan above

# 2. Create ZIP
python share_results.py \
    --scan-dir jenkins_scan_results/* \
    --create-zip

# 3. Send via email
# Attach the file: jenkins_scan_results/*.zip

# Or send automatically
python share_results.py \
    --scan-dir jenkins_scan_results/* \
    --email \
    --smtp-server smtp.company.com \
    --sender you@company.com \
    --recipients manager@company.com
```

---

### Tutorial 3: Weekly Automated Audit (10 minutes)

```bash
# 1. Create script
cat > weekly_audit.sh << 'EOF'
#!/bin/bash
python complete_scanner.py \
    --jenkins-url https://jenkins.company.com \
    --username $JENKINS_USER \
    --token $JENKINS_TOKEN \
    --parameters ECR_PATH AWS_REGION

# Send email
SCAN_DIR=$(ls -td jenkins_scan_results/* | head -1)
python share_results.py \
    --scan-dir $SCAN_DIR \
    --email \
    --smtp-server smtp.company.com \
    --sender jenkins-audit@company.com \
    --recipients team@company.com
EOF

# 2. Give permission
chmod +x weekly_audit.sh

# 3. Schedule with cron (every Monday 8am)
crontab -e
# Add:
# 0 8 * * 1 /path/to/weekly_audit.sh
```

---

## 🆕 Detailed New Features

### 1. Export Jenkins Configurations

**What it does:**
- Connects to Jenkins via API
- Downloads `config.xml` of ALL jobs
- Saves locally in organized manner
- Extracts metadata automatically

**Why it's useful:**
- ✅ Complete config backup
- ✅ Offline analysis
- ✅ Config version control
- ✅ Historical audit

**Usage:**
```bash
python jenkins_config_exporter.py \
    --jenkins-url https://jenkins.company.com \
    --username admin \
    --token abc123
```

---

### 2. Scan All Jobs Configs

**What it does:**
- Analyzes ALL exported configurations
- Searches multiple parameters simultaneously
- Differentiates defined parameters vs only used
- Counts occurrences

**Why it's useful:**
- ✅ Finds hardcoded values
- ✅ Identifies unused parameters
- ✅ Validates parameterization
- ✅ Migration support

**Usage:**
```bash
# Search multiple parameters
python complete_scanner.py \
    --jenkins-url ... \
    --parameters PARAM1 PARAM2 PARAM3 PARAM4
```

---

### 3. Share Results

**What it does:**
- Generates visual and interactive HTML report
- Exports CSV for Excel/Sheets
- Creates JSON for automation
- Sends email with attachments
- Creates shareable ZIP

**Why it's useful:**
- ✅ Facilitates management communication
- ✅ Allows analysis in known tools
- ✅ Automates distribution
- ✅ Permanent visual record

**Usage:**
```bash
# ZIP
python share_results.py --scan-dir DIR --create-zip

# Email
python share_results.py --scan-dir DIR --email \
    --smtp-server smtp.company.com \
    --sender from@company.com \
    --recipients to1@company.com to2@company.com
```

---

## 🎨 HTML Report - Features

The generated HTML report is professional and includes:

- 📊 **Visual dashboard** - Statistics in colored cards
- 🔍 **Real-time search** - Filters jobs instantly
- 📋 **Detailed tables** - One for each parameter
- 🔗 **Direct links** - Click to open job in Jenkins
- 🎨 **Modern design** - Gradients, shadows, hover effects
- 📱 **Responsive** - Works on desktop and mobile
- 🏷️ **Colored badges** - Quick visual status

**Colors:**
- Green = Working job
- Blue = Pipeline type
- Yellow = Warnings
- Red = Problems

---

## 🔒 Security

### API Token

**NEVER commit the token!**

```bash
# Good ✅
export JENKINS_TOKEN="abc123"
python complete_scanner.py --token $JENKINS_TOKEN

# Bad ❌
python complete_scanner.py --token abc123  # Token in history!

# Better ✅
# Use config.ini (not versioned)
python complete_scanner.py  # Reads from config.ini
```

### Sensitive Files

Add to `.gitignore`:
```
config.ini
jenkins_scan_results/
jenkins_exports/
*.xml
*.json
*.csv
```

---

## 🤝 Support

### Logs and Debug

```bash
# Verbose mode (add to script)
python complete_scanner.py ... --verbose

# Save logs
python complete_scanner.py ... 2>&1 | tee scan.log
```

### Common Issues

**"Connection refused"**
- Check Jenkins URL
- Try in browser first
- Check VPN/firewall

**"401 Unauthorized"**
- Invalid or expired token
- Generate new token
- Check username

**"Timeout"**
- Slow or offline Jenkins
- Increase timeout in code
- Run during off-peak hours

---

## 📊 Comparison with v1.0

| Feature | v1.0 | v2.0 |
|---------|------|------|
| Export configs | ❌ | ✅ |
| Scan via API | ✅ | ✅ |
| Scan via Git | ✅ | ✅ |
| HTML Report | ❌ | ✅ |
| CSV Export | ❌ | ✅ |
| JSON Export | ⚠️ Basic | ✅ Complete |
| Automatic email | ❌ | ✅ |
| Shareable ZIP | ❌ | ✅ |
| Multiple parameters | ⚠️ One at a time | ✅ Simultaneous |
| Interactive search | ❌ | ✅ |
| Modern design | ❌ | ✅ |

---

## 🗺️ Roadmap

### Upcoming Features

- [ ] Persistent web dashboard
- [ ] Historical comparison (drift detection)
- [ ] Slack/Teams integration
- [ ] Job dependency analysis
- [ ] Automatic optimization suggestions
- [ ] Export to Confluence/Notion
- [ ] Auto-generated documentation

---

## 📄 License

Tools provided "as is" for internal use.

---

## 🙏 Credits

Developed to facilitate audits and Jenkins pipeline management.

**Version:** 2.0  
**Date:** November 2024  
**Features:** Export, Scan, Share

---

## 🚀 Get Started Now

```bash
# 1. Install
pip install requests

# 2. Run
python complete_scanner.py \
    --jenkins-url https://your-jenkins.com \
    --username your_username \
    --token your_token \
    --parameters ECR_PATH

# 3. Open the report
firefox jenkins_scan_results/*/reports/report.html
```

**That's it! Simple as that.** 🎉

---

For more details, see:
- 📘 **EXPORT_SCAN_SHARE_GUIDE.md** - Complete guide
- 🏗️ **ARCHITECTURE_GUIDE.md** - Technical decisions
- ⚡ **QUICK_DECISION_GUIDE.md** - Quick start
- 📝 **EXAMPLES.md** - Practical examples
