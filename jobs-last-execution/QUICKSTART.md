# Quick Start Guide

## 3 Steps to Get Started

### 1. Configure Credentials

```bash
cp .env.example .env
nano .env  # Edit with your credentials
```

In `.env` file:
```
JENKINS_URL=https://jenkins.company.com
JENKINS_USER=your_username
JENKINS_TOKEN=your_api_token
```

### 2. Run the Script

```bash
# Option A: Using helper script (recommended)
./run_analyzer.sh

# Option B: Direct Python execution
python3 jenkins_inactive_jobs_analyzer.py
```

### 3. View Results

Reports will be in `jenkins_reports/`:
- 📊 **HTML**: Open in browser for interactive visualization
- 📄 **CSV**: Open in Excel/LibreOffice
- 🗂️ **JSON**: For programmatic processing

---

## Usage Examples

### Basic Analysis
```bash
./run_analyzer.sh
```

### Custom Output Directory
```bash
python3 jenkins_inactive_jobs_analyzer.py --output-dir /backup/jenkins_reports
```

### Without .env File
```bash
python3 jenkins_inactive_jobs_analyzer.py \
    --jenkins-url https://jenkins.company.com \
    --username admin \
    --token abc123xyz
```

---

## Tips

✅ **First run**: Use environment variables (.env file)  
✅ **Automation**: Use cron for periodic execution  
✅ **Security**: Never commit .env file to Git  
✅ **Performance**: For 500+ jobs, analysis may take a few minutes  

---

## Next Steps

After first execution:

1. **Review HTML report** for quick visualization
2. **Analyze CSVs** for data manipulation
3. **Identify jobs to archive/delete**
4. **Schedule periodic executions** (monthly/quarterly)

---

## Need Help?

Check **README.md** for:
- Troubleshooting
- Advanced parameters
- Use cases
- Security settings
