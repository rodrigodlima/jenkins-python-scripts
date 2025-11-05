#!/usr/bin/env python3
"""
Jenkins Inactive Jobs Analyzer
Analyzes all Jenkins jobs to identify inactive jobs and generate reports.
"""

import requests
from requests.auth import HTTPBasicAuth
import json
from datetime import datetime, timedelta
from pathlib import Path
import argparse
from typing import List, Dict, Optional
import csv


class JenkinsInactiveJobsAnalyzer:
    SIX_MONTHS_IN_DAYS = 180
    
    def __init__(self, jenkins_url: str, username: str, token: str):
        self.jenkins_url = jenkins_url.rstrip('/')
        self.auth = HTTPBasicAuth(username, token)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.six_months_ago = datetime.now() - timedelta(days=self.SIX_MONTHS_IN_DAYS)
        
    def get_all_jobs(self, folder_path: str = "") -> List[Dict]:
        jobs = []
        url = f"{self.jenkins_url}/{folder_path}api/json?tree=jobs[name,url,_class,jobs,color]"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            for job in data.get('jobs', []):
                job_class = job.get('_class', '')
                
                if 'Folder' in job_class or 'OrganizationFolder' in job_class:
                    folder_jobs = self.get_all_jobs(job['url'].replace(self.jenkins_url, ''))
                    jobs.extend(folder_jobs)
                else:
                    jobs.append(job)
                    
        except Exception as e:
            print(f"⚠️  Error getting jobs from {folder_path}: {e}")
            
        return jobs
    
    def get_job_details(self, job_url: str) -> Optional[Dict]:
        api_url = f"{job_url}api/json?tree=name,fullName,url,lastBuild[number,timestamp,result],lastSuccessfulBuild[timestamp],lastFailedBuild[timestamp],lastCompletedBuild[timestamp]"
        
        try:
            response = self.session.get(api_url, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"⚠️  Error getting job details from {job_url}: {e}")
            return None
    
    def timestamp_to_datetime(self, timestamp: Optional[int]) -> Optional[datetime]:
        if timestamp:
            return datetime.fromtimestamp(timestamp / 1000.0)
        return None
    
    def analyze_job(self, job_details: Dict) -> Dict:
        job_name = job_details.get('fullName', job_details.get('name', 'Unknown'))
        job_url = job_details.get('url', '')
        
        last_build = job_details.get('lastBuild')
        last_failed_build = job_details.get('lastFailedBuild')
        last_completed_build = job_details.get('lastCompletedBuild')
        
        last_build_date = None
        last_failure_date = None
        
        if last_build:
            last_build_date = self.timestamp_to_datetime(last_build.get('timestamp'))
        elif last_completed_build:
            last_build_date = self.timestamp_to_datetime(last_completed_build.get('timestamp'))
            
        if last_failed_build:
            last_failure_date = self.timestamp_to_datetime(last_failed_build.get('timestamp'))
        
        no_execution_6months = False
        no_failure_6months = False
        never_executed = False
        
        if last_build_date is None:
            never_executed = True
            no_execution_6months = True
        elif last_build_date < self.six_months_ago:
            no_execution_6months = True
        
        if last_failure_date and last_failure_date < self.six_months_ago:
            no_failure_6months = True
        
        days_since_execution = None
        days_since_failure = None
        
        if last_build_date:
            days_since_execution = (datetime.now() - last_build_date).days
            
        if last_failure_date:
            days_since_failure = (datetime.now() - last_failure_date).days
        
        return {
            'job_name': job_name,
            'job_url': job_url,
            'last_build_date': last_build_date,
            'last_failure_date': last_failure_date,
            'days_since_execution': days_since_execution,
            'days_since_failure': days_since_failure,
            'no_execution_6months': no_execution_6months,
            'no_failure_6months': no_failure_6months,
            'never_executed': never_executed
        }
    
    def analyze_all_jobs(self) -> Dict[str, List[Dict]]:
        print("🔍 Fetching all Jenkins jobs...")
        all_jobs = self.get_all_jobs()
        print(f"✅ Found {len(all_jobs)} jobs")
        
        print("\n📊 Analyzing jobs...")
        
        results = {
            'no_execution_6months': [],
            'no_failure_6months': [],
            'never_executed': [],
            'all_analyzed': []
        }
        
        for i, job in enumerate(all_jobs, 1):
            print(f"   Analyzing {i}/{len(all_jobs)}: {job['name']}", end='\r')
            
            job_details = self.get_job_details(job['url'])
            if job_details:
                analysis = self.analyze_job(job_details)
                results['all_analyzed'].append(analysis)
                
                if analysis['never_executed']:
                    results['never_executed'].append(analysis)
                elif analysis['no_execution_6months']:
                    results['no_execution_6months'].append(analysis)
                    
                if analysis['no_failure_6months']:
                    results['no_failure_6months'].append(analysis)
        
        print("\n✅ Analysis completed!")
        return results
    
    def generate_report(self, results: Dict[str, List[Dict]], output_dir: str = "jenkins_reports"):
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self._save_json_report(results, output_path, timestamp)
        self._save_csv_reports(results, output_path, timestamp)
        self._save_html_report(results, output_path, timestamp)
        self._print_summary(results)
    
    def _save_json_report(self, results: Dict, output_path: Path, timestamp: str):
        json_file = output_path / f"inactive_jobs_{timestamp}.json"
        
        json_results = {}
        for category, jobs in results.items():
            json_results[category] = []
            for job in jobs:
                job_copy = job.copy()
                if job_copy['last_build_date']:
                    job_copy['last_build_date'] = job_copy['last_build_date'].isoformat()
                if job_copy['last_failure_date']:
                    job_copy['last_failure_date'] = job_copy['last_failure_date'].isoformat()
                json_results[category].append(job_copy)
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_results, f, indent=2, ensure_ascii=False)
        
        print(f"\n📄 JSON report saved: {json_file}")
    
    def _save_csv_reports(self, results: Dict, output_path: Path, timestamp: str):
        csv_file = output_path / f"jobs_no_execution_6months_{timestamp}.csv"
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Job Name', 'URL', 'Last Execution', 'Days Since Execution', 'Status'])
            
            for job in results['no_execution_6months'] + results['never_executed']:
                status = 'Never executed' if job['never_executed'] else 'Inactive 6+ months'
                last_exec = job['last_build_date'].strftime('%Y-%m-%d') if job['last_build_date'] else 'Never'
                days = job['days_since_execution'] if job['days_since_execution'] else 'N/A'
                
                writer.writerow([
                    job['job_name'],
                    job['job_url'],
                    last_exec,
                    days,
                    status
                ])
        
        print(f"📄 CSV report (no execution) saved: {csv_file}")
        
        csv_file_failures = output_path / f"jobs_no_failure_6months_{timestamp}.csv"
        with open(csv_file_failures, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['Job Name', 'URL', 'Last Failure', 'Days Since Failure'])
            
            for job in results['no_failure_6months']:
                last_fail = job['last_failure_date'].strftime('%Y-%m-%d') if job['last_failure_date'] else 'Never'
                days = job['days_since_failure'] if job['days_since_failure'] else 'N/A'
                
                writer.writerow([
                    job['job_name'],
                    job['job_url'],
                    last_fail,
                    days
                ])
        
        print(f"📄 CSV report (old failures) saved: {csv_file_failures}")
    
    def _save_html_report(self, results: Dict, output_path: Path, timestamp: str):
        html_file = output_path / f"inactive_jobs_report_{timestamp}.html"
        html_content = self._generate_html_content(results)
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"📄 HTML report saved: {html_file}")
    
    def _generate_html_content(self, results: Dict) -> str:
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jenkins - Inactive Jobs Analysis</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin: 20px 0;
        }}
        .summary-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .summary-card.warning {{
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }}
        .summary-card.danger {{
            background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            font-size: 14px;
            opacity: 0.9;
        }}
        .summary-card .number {{
            font-size: 36px;
            font-weight: bold;
            margin: 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th {{
            background-color: #3498db;
            color: white;
            padding: 12px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .status-badge {{
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }}
        .status-never {{
            background-color: #e74c3c;
            color: white;
        }}
        .status-inactive {{
            background-color: #f39c12;
            color: white;
        }}
        .job-link {{
            color: #3498db;
            text-decoration: none;
        }}
        .job-link:hover {{
            text-decoration: underline;
        }}
        .timestamp {{
            color: #7f8c8d;
            font-size: 12px;
            margin-top: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Jenkins - Inactive Jobs Analysis</h1>
        <p class="timestamp">Generated on: {datetime.now().strftime('%Y-%m-%d at %H:%M:%S')}</p>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Total Jobs Analyzed</h3>
                <p class="number">{len(results['all_analyzed'])}</p>
            </div>
            <div class="summary-card warning">
                <h3>Inactive Jobs (6+ months)</h3>
                <p class="number">{len(results['no_execution_6months'])}</p>
            </div>
            <div class="summary-card danger">
                <h3>Never Executed Jobs</h3>
                <p class="number">{len(results['never_executed'])}</p>
            </div>
            <div class="summary-card">
                <h3>Old Last Failure (6+ months)</h3>
                <p class="number">{len(results['no_failure_6months'])}</p>
            </div>
        </div>
        
        <h2>🔴 Jobs Not Executed for 6+ Months</h2>
        <table>
            <thead>
                <tr>
                    <th>Job</th>
                    <th>Last Execution</th>
                    <th>Days Without Execution</th>
                    <th>Status</th>
                </tr>
            </thead>
            <tbody>
{self._generate_inactive_jobs_rows(results)}
            </tbody>
        </table>
        
        <h2>⚠️ Jobs with Last Failure 6+ Months Ago</h2>
        <table>
            <thead>
                <tr>
                    <th>Job</th>
                    <th>Last Failure</th>
                    <th>Days Since Last Failure</th>
                </tr>
            </thead>
            <tbody>
{self._generate_old_failures_rows(results)}
            </tbody>
        </table>
    </div>
</body>
</html>"""
    
    def _generate_inactive_jobs_rows(self, results: Dict) -> str:
        rows = []
        for job in sorted(results['no_execution_6months'] + results['never_executed'], 
                         key=lambda x: x['days_since_execution'] if x['days_since_execution'] else float('inf'), 
                         reverse=True):
            status = 'Never executed' if job['never_executed'] else 'Inactive'
            status_class = 'status-never' if job['never_executed'] else 'status-inactive'
            last_exec = job['last_build_date'].strftime('%Y-%m-%d') if job['last_build_date'] else 'Never'
            days = job['days_since_execution'] if job['days_since_execution'] else 'N/A'
            
            rows.append(f"""                <tr>
                    <td><a href="{job['job_url']}" class="job-link" target="_blank">{job['job_name']}</a></td>
                    <td>{last_exec}</td>
                    <td>{days}</td>
                    <td><span class="status-badge {status_class}">{status}</span></td>
                </tr>""")
        
        return '\n'.join(rows)
    
    def _generate_old_failures_rows(self, results: Dict) -> str:
        rows = []
        for job in sorted(results['no_failure_6months'], 
                         key=lambda x: x['days_since_failure'] if x['days_since_failure'] else 0, 
                         reverse=True):
            last_fail = job['last_failure_date'].strftime('%Y-%m-%d') if job['last_failure_date'] else 'Never'
            days = job['days_since_failure'] if job['days_since_failure'] else 'N/A'
            
            rows.append(f"""                <tr>
                    <td><a href="{job['job_url']}" class="job-link" target="_blank">{job['job_name']}</a></td>
                    <td>{last_fail}</td>
                    <td>{days}</td>
                </tr>""")
        
        return '\n'.join(rows)
    
    def _print_summary(self, results: Dict):
        print("\n" + "="*60)
        print("📊 ANALYSIS SUMMARY")
        print("="*60)
        print(f"Total jobs analyzed: {len(results['all_analyzed'])}")
        print(f"Inactive jobs (6+ months): {len(results['no_execution_6months'])}")
        print(f"Never executed jobs: {len(results['never_executed'])}")
        print(f"Jobs with old last failure (6+ months): {len(results['no_failure_6months'])}")
        print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description='Analyze inactive jobs in Jenkins',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:

  # Using environment variables
  export JENKINS_URL="https://jenkins.company.com"
  export JENKINS_USER="your_username"
  export JENKINS_TOKEN="your_token"
  python jenkins_inactive_jobs_analyzer.py

  # Passing parameters directly
  python jenkins_inactive_jobs_analyzer.py \\
      --jenkins-url https://jenkins.company.com \\
      --username your_username \\
      --token your_token

  # Specifying output directory
  python jenkins_inactive_jobs_analyzer.py \\
      --jenkins-url https://jenkins.company.com \\
      --username your_username \\
      --token your_token \\
      --output-dir /path/to/reports
        """
    )
    
    parser.add_argument(
        '--jenkins-url',
        default=None,
        help='Jenkins URL (e.g., https://jenkins.company.com)'
    )
    parser.add_argument(
        '--username',
        default=None,
        help='Jenkins username'
    )
    parser.add_argument(
        '--token',
        default=None,
        help='Jenkins API token'
    )
    parser.add_argument(
        '--output-dir',
        default='jenkins_reports',
        help='Directory to save reports (default: jenkins_reports)'
    )
    
    args = parser.parse_args()
    
    import os
    jenkins_url = args.jenkins_url or os.getenv('JENKINS_URL')
    username = args.username or os.getenv('JENKINS_USER')
    token = args.token or os.getenv('JENKINS_TOKEN')
    
    if not all([jenkins_url, username, token]):
        print("❌ Error: Jenkins URL, username, and token are required")
        print("\nProvide credentials via:")
        print("1. Parameters: --jenkins-url, --username, --token")
        print("2. Environment variables: JENKINS_URL, JENKINS_USER, JENKINS_TOKEN")
        return
    
    print("="*60)
    print("🚀 Jenkins Inactive Jobs Analyzer")
    print("="*60)
    print(f"Jenkins URL: {jenkins_url}")
    print(f"Username: {username}")
    print(f"Reports will be saved to: {args.output_dir}")
    print("="*60)
    
    analyzer = JenkinsInactiveJobsAnalyzer(jenkins_url, username, token)
    results = analyzer.analyze_all_jobs()
    analyzer.generate_report(results, args.output_dir)
    
    print("\n✅ Analysis completed successfully!")


if __name__ == '__main__':
    main()
