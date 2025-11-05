# Jenkins Inactive Jobs Analyzer

Python script to analyze Jenkins jobs and identify:
- ✅ Jobs not executed for 6+ months
- ✅ Jobs never executed
- ✅ Jobs whose last failure was 6+ months ago

## Features

- **Complete Analysis**: Scans all Jenkins jobs recursively (including folders)
- **Multiple Formats**: Generates reports in JSON, CSV, and HTML
- **Visual Dashboard**: Interactive HTML report with charts
- **Easy to Use**: Supports environment variables or direct parameters
- **Fast**: Efficient parallel processing

## Prerequisites

- Python 3.7+
- Jenkins access with API token
- Read permissions on jobs

## Installation

```bash
pip install -r requirements.txt
```

## Getting Jenkins API Token

1. Access your Jenkins instance
2. Click on your username (top right)
3. Click "Configure"
4. In "API Token" section, click "Add new Token"
5. Give it a name and click "Generate"
6. **Copy the generated token** (you won't be able to see it again!)

## Usage

### Option 1: Using Environment Variables (Recommended)

```bash
export JENKINS_URL="https://jenkins.company.com"
export JENKINS_USER="your_username"
export JENKINS_TOKEN="your_api_token"

python jenkins_inactive_jobs_analyzer.py
```

### Option 2: Direct Parameters

```bash
python jenkins_inactive_jobs_analyzer.py \
    --jenkins-url https://jenkins.company.com \
    --username your_username \
    --token your_api_token
```

### Option 3: Custom Output Directory

```bash
python jenkins_inactive_jobs_analyzer.py \
    --jenkins-url https://jenkins.company.com \
    --username your_username \
    --token your_api_token \
    --output-dir /path/to/reports
```

## Output

The script generates 4 types of files in `jenkins_reports/`:

### 1. JSON Report (`inactive_jobs_YYYYMMDD_HHMMSS.json`)
```json
{
  "no_execution_6months": [...],
  "no_failure_6months": [...],
  "never_executed": [...],
  "all_analyzed": [...]
}
```

### 2. CSV - Jobs Without Execution (`jobs_no_execution_6months_YYYYMMDD_HHMMSS.csv`)
```csv
Job Name,URL,Last Execution,Days Since Execution,Status
project-x,https://...,2024-01-15,294,Inactive 6+ months
project-y,https://...,Never,N/A,Never executed
```

### 3. CSV - Jobs with Old Failures (`jobs_no_failure_6months_YYYYMMDD_HHMMSS.csv`)
```csv
Job Name,URL,Last Failure,Days Since Failure
project-z,https://...,2024-02-20,258
```

### 4. HTML Report (`inactive_jobs_report_YYYYMMDD_HHMMSS.html`)
- Visual dashboard with statistics
- Interactive tables
- Direct links to jobs
- Color-coded formatting
- Responsive design

## Example Output

```
==============================================================
🚀 Jenkins Inactive Jobs Analyzer
==============================================================
Jenkins URL: https://jenkins.company.com
Username: admin
Reports will be saved to: jenkins_reports
==============================================================
🔍 Fetching all Jenkins jobs...
✅ Found 234 jobs

📊 Analyzing jobs...
   Analyzing 234/234: final-project
✅ Analysis completed!

📄 JSON report saved: jenkins_reports/inactive_jobs_20241105_143022.json
📄 CSV report (no execution) saved: jenkins_reports/jobs_no_execution_6months_20241105_143022.csv
📄 CSV report (old failures) saved: jenkins_reports/jobs_no_failure_6months_20241105_143022.csv
📄 HTML report saved: jenkins_reports/inactive_jobs_report_20241105_143022.html

============================================================
📊 ANALYSIS SUMMARY
============================================================
Total jobs analyzed: 234
Inactive jobs (6+ months): 45
Never executed jobs: 12
Jobs with old last failure (6+ months): 23
============================================================

✅ Analysis completed successfully!
```

## Viewing Reports

### HTML Report (Recommended)

Open in any browser:

```bash
firefox jenkins_reports/inactive_jobs_report_*.html
# or
google-chrome jenkins_reports/inactive_jobs_report_*.html
# or
open jenkins_reports/inactive_jobs_report_*.html  # macOS
```

### CSV Reports

Open with Excel, LibreOffice, or any spreadsheet editor:

```bash
libreoffice jenkins_reports/jobs_no_execution_6months_*.csv
```

## Parameters

| Parameter | Environment Variable | Description | Required |
|-----------|---------------------|-------------|----------|
| `--jenkins-url` | `JENKINS_URL` | Jenkins URL | ✅ Yes |
| `--username` | `JENKINS_USER` | Jenkins username | ✅ Yes |
| `--token` | `JENKINS_TOKEN` | API token | ✅ Yes |
| `--output-dir` | - | Output directory | ❌ No (default: jenkins_reports) |

## Analysis Criteria

### 🔴 Inactive (6+ months)
- Last execution was more than 180 days ago
- May have executed in the past but stopped long ago

### ⚫ Never Executed
- Job was created but never had any execution
- May be a test job or abandoned

### ⚠️ Old Last Failure (6+ months)
- Last failure was more than 180 days ago
- May indicate job is working well OR not executing

## Troubleshooting

### Error: "Jenkins URL, username, and token are required"

**Solution**: Provide credentials via parameters or environment variables.

### Error: "requests.exceptions.SSLError"

**Solution**: If using self-signed certificate, modify the script to disable SSL verification (not recommended for production):

```python
response = self.session.get(url, timeout=30, verify=False)
```

### Error: "403 Forbidden" or "401 Unauthorized"

**Solutions**:
1. Verify token is correct
2. Check user has read permissions on jobs
3. Try generating a new API token

## Security

**⚠️ IMPORTANT**: 

- Never commit API token to Git
- Use environment variables for credentials
- Consider using a token with minimal permissions (read-only)
- Revoke unused tokens regularly

## Use Cases

### 1. Job Cleanup
Identify inactive jobs to archive or delete, freeing Jenkins resources.

### 2. Audit
Generate periodic reports for governance meetings.

### 3. Preventive Maintenance
Identify abandoned jobs before they become a problem.

### 4. Migration
List all inactive jobs before migrating to a new Jenkins server.

## Automation

Schedule periodic execution with cron:

```bash
# Monthly execution (first day of month at 2 AM)
0 2 1 * * cd /path/to/script && ./run_analyzer.sh >> /var/log/jenkins_analyzer.log 2>&1
```

See `AUTOMATION.md` for detailed automation examples.

## License

This script is provided "as is", without warranties. Use at your own risk.

---

**Developed for efficient Jenkins jobs analysis** 🚀
