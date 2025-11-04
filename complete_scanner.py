#!/usr/bin/env python3
"""
Jenkins Complete Scanner & Exporter
Exports configs + Parameter scan + Shareable reports (HTML, CSV)
"""

import requests
import json
import csv
from pathlib import Path
from typing import List, Dict
from requests.auth import HTTPBasicAuth
import argparse
from datetime import datetime
import xml.etree.ElementTree as ET


class JenkinsCompleteScanner:
    def __init__(self, jenkins_url: str, username: str, token: str, 
                 output_dir: str = "jenkins_scan_results", git_repos_path: str = None):
        """
        Complete scanner with export and reports
        """
        self.jenkins_url = jenkins_url.rstrip('/')
        self.auth = HTTPBasicAuth(username, token)
        self.session = requests.Session()
        self.session.auth = self.auth
        
        self.output_dir = Path(output_dir)
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.scan_dir = self.output_dir / self.timestamp
        
        # Creates estrutura
        (self.scan_dir / "configs").mkdir(parents=True, exist_ok=True)
        (self.scan_dir / "reports").mkdir(parents=True, exist_ok=True)
        (self.scan_dir / "exports").mkdir(parents=True, exist_ok=True)
        
        self.git_repos_path = Path(git_repos_path) if git_repos_path else None
        
    def get_all_jobs(self, folder_path: str = "") -> List[Dict]:
        """Gets all jobs recursively"""
        jobs = []
        url = f"{self.jenkins_url}/{folder_path}api/json?tree=jobs[name,url,_class,color,description]"
        
        try:
            response = self.session.get(url, verify=True)
            response.raise_for_status()
            data = response.json()
            
            for job in data.get('jobs', []):
                job_class = job.get('_class', '')
                
                if 'Folder' in job_class:
                    sub_jobs = self.get_all_jobs(job['url'].replace(self.jenkins_url, ''))
                    jobs.extend(sub_jobs)
                else:
                    jobs.append(job)
                    
        except Exception as e:
            print(f"  ⚠ Error: {str(e)}")
            
        return jobs
    
    def get_job_config(self, job_url: str) -> str:
        """Gets config XML"""
        try:
            response = self.session.get(f"{job_url}config.xml", verify=True)
            response.raise_for_status()
            return response.text
        except:
            return ""
    
    def analyze_job(self, job: Dict, parameters: List[str]) -> Dict:
        """
        Analyzes job completo
        """
        job_name = job.get('name')
        job_url = job.get('url')
        
        result = {
            'job_name': job_name,
            'job_url': job_url,
            'status': job.get('color', 'unknown'),
            'description': job.get('description', ''),
            'config_exported': False,
            'parameters_found': {},
            'metadata': {}
        }
        
        # Gets e salva config
        config_xml = self.get_job_config(job_url)
        if config_xml:
            # Saves config
            safe_name = job_name.replace('/', '_').replace(' ', '_')
            config_file = self.scan_dir / "configs" / f"{safe_name}.xml"
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(config_xml)
            result['config_exported'] = True
            result['config_file'] = str(config_file)
            
            # Analyzes
            result['metadata'] = self.extract_metadata(config_xml)
            
            # Searches parameters
            for param in parameters:
                result['parameters_found'][param] = self.search_parameter(config_xml, param)
        
        return result
    
    def extract_metadata(self, config_xml: str) -> Dict:
        """Extracts metadata of job"""
        metadata = {
            'type': 'unknown',
            'pipeline_type': None,
            'git_url': None,
            'jenkinsfile_path': None,
            'has_parameters': False,
            'defined_parameters': []
        }
        
        try:
            root = ET.fromstring(config_xml)
            metadata['type'] = root.tag
            
            # Pipeline
            if root.tag == 'flow-definition':
                definition = root.find('.//definition')
                if definition is not None:
                    def_class = definition.get('class', '')
                    if 'CpsFlowDefinition' in def_class:
                        metadata['pipeline_type'] = 'inline'
                    elif 'CpsScmFlowDefinition' in def_class:
                        metadata['pipeline_type'] = 'scm'
                        
                        scm = definition.find('.//scm')
                        if scm is not None:
                            url_elem = scm.find('.//url')
                            if url_elem is not None:
                                metadata['git_url'] = url_elem.text
                        
                        script_path = definition.find('.//scriptPath')
                        if script_path is not None:
                            metadata['jenkinsfile_path'] = script_path.text
            
            # Parameters definidos
            params = root.findall('.//hudson.model.StringParameterDefinition/name')
            params += root.findall('.//hudson.model.BooleanParameterDefinition/name')
            params += root.findall('.//hudson.model.ChoiceParameterDefinition/name')
            
            for param in params:
                if param.text:
                    metadata['defined_parameters'].append(param.text)
            
            if metadata['defined_parameters']:
                metadata['has_parameters'] = True
                
        except:
            pass
        
        return metadata
    
    def search_parameter(self, config_xml: str, parameter_name: str) -> Dict:
        """Searches parameter in XML"""
        import re
        
        result = {
            'found': False,
            'defined_as_parameter': False,
            'used_in_script': False,
            'occurrences': 0
        }
        
        # Definido como parameter
        if f'<name>{parameter_name}</name>' in config_xml:
            result['defined_as_parameter'] = True
            result['found'] = True
        
        # Usesdo no script
        patterns = [
            rf'\${{?{parameter_name}}}?',
            rf'params\.{parameter_name}',
            rf'env\.{parameter_name}'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, config_xml)
            if matches:
                result['used_in_script'] = True
                result['found'] = True
                result['occurrences'] += len(matches)
        
        return result
    
    def scan_all(self, parameters: List[str]) -> List[Dict]:
        """
        Scan complete de all jobs
        """
        print("=" * 80)
        print("🔍 JENKINS COMPLETE SCAN")
        print("=" * 80)
        print(f"Jenkins: {self.jenkins_url}")
        print(f"Parameters: {', '.join(parameters)}")
        print(f"Output: {self.scan_dir}")
        print("-" * 80)
        
        # Searches jobs
        print("\n📋 Searchesnof jobs...")
        all_jobs = self.get_all_jobs()
        print(f"✓ Founds: {len(all_jobs)} jobs")
        
        # Analyzes cada job
        print(f"\n🔎 Analyzesnof jobs...")
        print("-" * 80)
        
        results = []
        for idx, job in enumerate(all_jobs, 1):
            job_name = job.get('name')
            print(f"[{idx}/{len(all_jobs)}] {job_name[:60]}", end=" ... ")
            
            result = self.analyze_job(job, parameters)
            results.append(result)
            
            # Show found parameters
            found_params = [p for p in parameters if result['parameters_found'].get(p, {}).get('found')]
            if found_params:
                print(f"✓ [{', '.join(found_params)}]")
            else:
                print("○")
        
        print("-" * 80)
        print(f"\n✓ Scan complete!")
        
        return results
    
    def generate_html_report(self, results: List[Dict], parameters: List[str]):
        """Generates report HTML interativo"""
        html_file = self.scan_dir / "reports" / "report.html"
        
        # Statistics
        total_jobs = len(results)
        exported_configs = sum(1 for r in results if r['config_exported'])
        
        stats_by_param = {}
        for param in parameters:
            stats_by_param[param] = {
                'jobs_with_param': sum(1 for r in results if r['parameters_found'].get(param, {}).get('found')),
                'defined': sum(1 for r in results if r['parameters_found'].get(param, {}).get('defined_as_parameter')),
                'used_only': sum(1 for r in results 
                                if r['parameters_found'].get(param, {}).get('used_in_script') 
                                and not r['parameters_found'].get(param, {}).get('defined_as_parameter'))
            }
        
        html_content = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Jenkins Scan Report - {self.timestamp}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }}
        .header .subtitle {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f8f9fa;
        }}
        .stat-card {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.2s;
        }}
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.15);
        }}
        .stat-number {{
            font-size: 3em;
            font-weight: bold;
            color: #667eea;
            line-height: 1;
            margin-bottom: 10px;
        }}
        .stat-label {{
            color: #6c757d;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .parameters-section {{
            padding: 40px;
        }}
        .parameter-block {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 30px;
            margin-bottom: 30px;
            border-left: 5px solid #667eea;
        }}
        .parameter-title {{
            font-size: 1.8em;
            color: #667eea;
            margin-bottom: 20px;
            font-weight: 600;
        }}
        .parameter-stats {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }}
        .mini-stat {{
            background: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        .mini-stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }}
        .mini-stat-label {{
            color: #6c757d;
            font-size: 0.85em;
            margin-top: 5px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: white;
            border-radius: 8px;
            overflow: hidden;
        }}
        th {{
            background: #667eea;
            color: white;
            padding: 15px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 12px 15px;
            border-bottom: 1px solid #e9ecef;
        }}
        tr:hover {{
            background: #f8f9fa;
        }}
        .badge {{
            display: inline-block;
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }}
        .badge-success {{
            background: #28a745;
            color: white;
        }}
        .badge-warning {{
            background: #ffc107;
            color: #333;
        }}
        .badge-info {{
            background: #17a2b8;
            color: white;
        }}
        .badge-secondary {{
            background: #6c757d;
            color: white;
        }}
        .footer {{
            background: #2c3e50;
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .search-box {{
            padding: 20px;
            background: #f8f9fa;
            margin: 20px 40px;
            border-radius: 8px;
        }}
        .search-box input {{
            width: 100%;
            padding: 12px 20px;
            border: 2px solid #ddd;
            border-radius: 6px;
            font-size: 1em;
            transition: border-color 0.3s;
        }}
        .search-box input:focus {{
            outline: none;
            border-color: #667eea;
        }}
        .job-url {{
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }}
        .job-url:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔍 Jenkins Scan Report</h1>
            <div class="subtitle">
                {self.jenkins_url}<br>
                Generated on: {datetime.now().strftime('%d/%m/%Y at %H:%M:%S')}
            </div>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{total_jobs}</div>
                <div class="stat-label">Total Jobs</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{exported_configs}</div>
                <div class="stat-label">Configs Exportsdas</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{len(parameters)}</div>
                <div class="stat-label">Parameters Searchesdos</div>
            </div>
        </div>

        <div class="search-box">
            <input type="text" id="searchInput" placeholder="🔍 Searchesr jobs..." onkeyup="filterTable()">
        </div>

        <div class="parameters-section">
"""
        
        # Section for each parameter
        for param in parameters:
            stats = stats_by_param[param]
            jobs_with_param = [r for r in results if r['parameters_found'].get(param, {}).get('found')]
            
            html_content += f"""
            <div class="parameter-block">
                <div class="parameter-title">📌 {param}</div>
                
                <div class="parameter-stats">
                    <div class="mini-stat">
                        <div class="mini-stat-number">{stats['jobs_with_param']}</div>
                        <div class="mini-stat-label">Jobs com este parameter</div>
                    </div>
                    <div class="mini-stat">
                        <div class="mini-stat-number">{stats['defined']}</div>
                        <div class="mini-stat-label">Definido como parameter</div>
                    </div>
                    <div class="mini-stat">
                        <div class="mini-stat-number">{stats['used_only']}</div>
                        <div class="mini-stat-label">Usado apenas no script</div>
                    </div>
                </div>

                <table>
                    <thead>
                        <tr>
                            <th>Job Name</th>
                            <th>Status</th>
                            <th>Tipo</th>
                            <th>Definido</th>
                            <th>Usado</th>
                            <th>Occurrences</th>
                        </tr>
                    </thead>
                    <tbody>
"""
            
            for r in jobs_with_param:
                param_info = r['parameters_found'][param]
                status_color = 'success' if 'blue' in r['status'] else 'secondary'
                pipeline_type = r['metadata'].get('pipeline_type', 'N/A')
                
                html_content += f"""
                        <tr>
                            <td><a href="{r['job_url']}" class="job-url" target="_blank">{r['job_name']}</a></td>
                            <td><span class="badge badge-{status_color}">{r['status']}</span></td>
                            <td><span class="badge badge-info">{pipeline_type}</span></td>
                            <td>{'✓' if param_info['defined_as_parameter'] else '✗'}</td>
                            <td>{'✓' if param_info['used_in_script'] else '✗'}</td>
                            <td>{param_info['occurrences']}</td>
                        </tr>
"""
            
            html_content += """
                    </tbody>
                </table>
            </div>
"""
        
        html_content += f"""
        </div>

        <div class="footer">
            <p><strong>Jenkins Complete Scanner</strong></p>
            <p>Export Directory: {self.scan_dir}</p>
        </div>
    </div>

    <script>
        function filterTable() {{
            const input = document.getElementById('searchInput');
            const filter = input.value.toLowerCase();
            const tables = document.querySelectorAll('table');
            
            tables.forEach(table => {{
                const rows = table.getElementsByTagName('tr');
                for (let i = 1; i < rows.length; i++) {{
                    const row = rows[i];
                    const text = row.textContent.toLowerCase();
                    row.style.display = text.includes(filter) ? '' : 'none';
                }}
            }});
        }}
    </script>
</body>
</html>
"""
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"\n✓ Report HTML: {html_file}")
        return html_file
    
    def generate_csv_export(self, results: List[Dict], parameters: List[str]):
        """Generates export CSV"""
        csv_file = self.scan_dir / "exports" / "jobs_parameters.csv"
        
        with open(csv_file, 'w', newline='', encoding='utf-8') as f:
            fieldnames = ['Job Name', 'Job URL', 'Status', 'Pipeline Type', 'Git URL']
            for param in parameters:
                fieldnames.extend([
                    f'{param}_Found',
                    f'{param}_Defined',
                    f'{param}_Used',
                    f'{param}_Occurrences'
                ])
            
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for r in results:
                row = {
                    'Job Name': r['job_name'],
                    'Job URL': r['job_url'],
                    'Status': r['status'],
                    'Pipeline Type': r['metadata'].get('pipeline_type', 'N/A'),
                    'Git URL': r['metadata'].get('git_url', 'N/A')
                }
                
                for param in parameters:
                    param_info = r['parameters_found'].get(param, {})
                    row[f'{param}_Found'] = 'Yes' if param_info.get('found') else 'No'
                    row[f'{param}_Defined'] = 'Yes' if param_info.get('defined_as_parameter') else 'No'
                    row[f'{param}_Used'] = 'Yes' if param_info.get('used_in_script') else 'No'
                    row[f'{param}_Occurrences'] = param_info.get('occurrences', 0)
                
                writer.writerow(row)
        
        print(f"✓ CSV Export: {csv_file}")
        return csv_file
    
    def generate_json_export(self, results: List[Dict], parameters: List[str]):
        """Generates export JSON completa"""
        json_file = self.scan_dir / "exports" / "complete_scan.json"
        
        export_data = {
            'scan_timestamp': self.timestamp,
            'jenkins_url': self.jenkins_url,
            'parameters_searched': parameters,
            'total_jobs': len(results),
            'jobs': results
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ JSON Export: {json_file}")
        return json_file
    
    def generate_summary(self, results: List[Dict], parameters: List[str]):
        """Generates resumo em texto"""
        summary_file = self.scan_dir / "reports" / "summary.txt"
        
        lines = []
        lines.append("=" * 80)
        lines.append("JENKINS SCAN SUMMARY")
        lines.append("=" * 80)
        lines.append(f"\nTimestamp: {self.timestamp}")
        lines.append(f"Jenkins: {self.jenkins_url}")
        lines.append(f"Total Jobs: {len(results)}")
        lines.append(f"Parameters: {', '.join(parameters)}")
        
        for param in parameters:
            lines.append(f"\n{'─' * 80}")
            lines.append(f"Parameter: {param}")
            lines.append(f"{'─' * 80}")
            
            jobs_with = [r for r in results if r['parameters_found'].get(param, {}).get('found')]
            defined = [r for r in jobs_with if r['parameters_found'][param]['defined_as_parameter']]
            used_only = [r for r in jobs_with if r['parameters_found'][param]['used_in_script'] 
                        and not r['parameters_found'][param]['defined_as_parameter']]
            
            lines.append(f"  Jobs with parameter: {len(jobs_with)}")
            lines.append(f"  Defined as parameter: {len(defined)}")
            lines.append(f"  Used only in script: {len(used_only)}")
            
            if used_only:
                lines.append(f"\n  ⚠️  Jobs using {param} without defining it:")
                for r in used_only[:10]:
                    lines.append(f"    • {r['job_name']}")
                if len(used_only) > 10:
                    lines.append(f"    ... and {len(used_only) - 10} more")
        
        lines.append(f"\n{'=' * 80}")
        lines.append(f"Files generated:")
        lines.append(f"  • Configs: {self.scan_dir / 'configs'}")
        lines.append(f"  • Reports: {self.scan_dir / 'reports'}")
        lines.append(f"  • Exports: {self.scan_dir / 'exports'}")
        lines.append("=" * 80)
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        for line in lines:
            print(line)
        
        return summary_file


def main():
    parser = argparse.ArgumentParser(
        description='Jenkins Complete Scanner - Export + Scan + Share',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Este script faz 3 coisas:
  1. EXPORT: Exports todas as configurations of jobs
  2. SCAN: Searches parameters em all jobs
  3. SHARE: Generates reports compartilháveis (HTML, CSV, JSON)

Examples:

  # Basic scan
  python complete_scanner.py \\
      --jenkins-url https://jenkins.empresa.com \\
      --username admin \\
      --token abc123 \\
      --parameters ECR_PATH AWS_REGION

  # Com output customizado
  python complete_scanner.py \\
      --jenkins-url https://jenkins.empresa.com \\
      --username admin \\
      --token abc123 \\
      --parameters ECR_PATH \\
      --output-dir /backup/jenkins-scan
        """
    )
    
    parser.add_argument('--jenkins-url', required=True, help='URL do Jenkins')
    parser.add_argument('--username', required=True, help='Username')
    parser.add_argument('--token', required=True, help='Token API')
    parser.add_argument('--parameters', nargs='+', default=['ECR_PATH'], 
                       help='Parameters to search (space-separated)')
    parser.add_argument('--output-dir', default='jenkins_scan_results',
                       help='Directory de saída')
    parser.add_argument('--git-repos-path', help='Path repos Git (opcional)')
    
    args = parser.parse_args()
    
    try:
        scanner = JenkinsCompleteScanner(
            jenkins_url=args.jenkins_url,
            username=args.username,
            token=args.token,
            output_dir=args.output_dir,
            git_repos_path=args.git_repos_path
        )
        
        # Executes scan
        results = scanner.scan_all(args.parameters)
        
        # Generates reports
        print("\n" + "=" * 80)
        print("📊 GENERATING REPORTS")
        print("=" * 80)
        
        scanner.generate_html_report(results, args.parameters)
        scanner.generate_csv_export(results, args.parameters)
        scanner.generate_json_export(results, args.parameters)
        scanner.generate_summary(results, args.parameters)
        
        print("\n" + "=" * 80)
        print("✅ SCAN COMPLETO!")
        print("=" * 80)
        print(f"\n📁 Todos os files em: {scanner.scan_dir}")
        print(f"\n🌐 Open the HTML report:")
        print(f"   file://{scanner.scan_dir / 'reports' / 'report.html'}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Cancelled")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
