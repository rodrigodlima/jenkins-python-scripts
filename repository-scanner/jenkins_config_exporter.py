#!/usr/bin/env python3
"""
Jenkins Configuration Exporter
Exports configurations de all jobs do Jenkins para files locais
"""

import requests
import json
import os
from pathlib import Path
from typing import List, Dict
from urllib.parse import urljoin
from requests.auth import HTTPBasicAuth
import argparse
from datetime import datetime
import xml.etree.ElementTree as ET


class JenkinsConfigExporter:
    def __init__(self, jenkins_url: str, username: str, token: str, export_dir: str = "jenkins_exports"):
        """
        Initializes o exportador de configurations
        
        Args:
            jenkins_url: URL base do Jenkins
            username: Username do Jenkins
            token: Token de API
            export_dir: Directory para salvar exportações
        """
        self.jenkins_url = jenkins_url.rstrip('/')
        self.auth = HTTPBasicAuth(username, token)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.export_dir = Path(export_dir)
        self.export_dir.mkdir(parents=True, exist_ok=True)
        
        # Creates estrutura de directorys
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.current_export = self.export_dir / self.timestamp
        self.current_export.mkdir(parents=True, exist_ok=True)
        
        (self.current_export / "configs").mkdir(exist_ok=True)
        (self.current_export / "reports").mkdir(exist_ok=True)
        
    def get_all_jobs(self, folder_path: str = "") -> List[Dict]:
        """Gets all jobs do Jenkins recursively"""
        jobs = []
        url = f"{self.jenkins_url}/{folder_path}api/json?tree=jobs[name,url,_class,jobs,color,description]"
        
        try:
            response = self.session.get(url, verify=True)
            response.raise_for_status()
            data = response.json()
            
            for job in data.get('jobs', []):
                job_class = job.get('_class', '')
                
                if 'Folder' in job_class or 'OrganizationFolder' in job_class:
                    sub_jobs = self.get_all_jobs(job['url'].replace(self.jenkins_url, ''))
                    jobs.extend(sub_jobs)
                else:
                    jobs.append(job)
                    
        except Exception as e:
            print(f"  ⚠ Error getting jobs de {folder_path}: {str(e)}")
            
        return jobs
    
    def get_job_config(self, job_url: str) -> str:
        """Gets a configuration XML of job"""
        config_url = f"{job_url}config.xml"
        try:
            response = self.session.get(config_url, verify=True)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"  ⚠ Error getting config: {str(e)}")
            return ""
    
    def sanitize_filename(self, name: str) -> str:
        """Removes invalid characters do nome do file"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        return name
    
    def export_job_config(self, job: Dict) -> Dict:
        """
        Exports configuration de um job
        
        Returns:
            Dict com informações da exportação
        """
        job_name = job.get('name')
        job_url = job.get('url')
        
        result = {
            'job_name': job_name,
            'job_url': job_url,
            'status': 'failed',
            'config_file': None,
            'metadata': {}
        }
        
        try:
            # Gets configuration
            config_xml = self.get_job_config(job_url)
            if not config_xml:
                return result
            
            # Saves XML
            safe_name = self.sanitize_filename(job_name)
            config_file = self.current_export / "configs" / f"{safe_name}.xml"
            
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(config_xml)
            
            result['config_file'] = str(config_file)
            result['status'] = 'success'
            
            # Extracts metadata
            try:
                root = ET.fromstring(config_xml)
                result['metadata'] = {
                    'type': root.tag,
                    'description': job.get('description', ''),
                    'color': job.get('color', ''),
                    'class': job.get('_class', '')
                }
                
                # Detects tipo de pipeline
                if root.tag == 'flow-definition':
                    definition = root.find('.//definition')
                    if definition is not None:
                        def_class = definition.get('class', '')
                        if 'CpsFlowDefinition' in def_class:
                            result['metadata']['pipeline_type'] = 'inline'
                        elif 'CpsScmFlowDefinition' in def_class:
                            result['metadata']['pipeline_type'] = 'scm'
                            
                            # Git URL
                            scm = definition.find('.//scm')
                            if scm is not None:
                                url_elem = scm.find('.//url')
                                if url_elem is not None:
                                    result['metadata']['git_url'] = url_elem.text
                            
                            # Jenkinsfile path
                            script_path = definition.find('.//scriptPath')
                            if script_path is not None:
                                result['metadata']['jenkinsfile_path'] = script_path.text
                
            except Exception as e:
                print(f"  ⚠ Error extracting metadata de {job_name}: {str(e)}")
            
        except Exception as e:
            print(f"  ❌ Error ao exportar {job_name}: {str(e)}")
        
        return result
    
    def export_all_configs(self) -> List[Dict]:
        """
        Exports configurations de all jobs
        
        Returns:
            Lista com resultados das exportações
        """
        print("=" * 80)
        print("📦 EXPORTING JENKINS CONFIGURATIONS")
        print("=" * 80)
        print(f"Jenkins: {self.jenkins_url}")
        print(f"Export directory: {self.current_export}")
        print("-" * 80)
        
        # Gets all jobs
        print("\n🔍 Searchesnof jobs...")
        all_jobs = self.get_all_jobs()
        print(f"✓ Total jobs encontrados: {len(all_jobs)}")
        
        print("\n📥 Exportsndo configurations...")
        print("-" * 80)
        
        results = []
        success_count = 0
        
        for idx, job in enumerate(all_jobs, 1):
            job_name = job.get('name')
            print(f"[{idx}/{len(all_jobs)}] {job_name}", end=" ... ")
            
            result = self.export_job_config(job)
            results.append(result)
            
            if result['status'] == 'success':
                print("✓")
                success_count += 1
            else:
                print("✗")
        
        print("-" * 80)
        print(f"\n✓ Export completed!")
        print(f"  Success: {success_count}/{len(all_jobs)}")
        print(f"  Failures: {len(all_jobs) - success_count}")
        
        # Saves índice
        self.save_export_index(results)
        
        return results
    
    def save_export_index(self, results: List[Dict]):
        """Saves índice das exportações"""
        index_file = self.current_export / "export_index.json"
        
        index_data = {
            'export_timestamp': self.timestamp,
            'jenkins_url': self.jenkins_url,
            'total_jobs': len(results),
            'successful_exports': sum(1 for r in results if r['status'] == 'success'),
            'failed_exports': sum(1 for r in results if r['status'] == 'failed'),
            'jobs': results
        }
        
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Index saved to: {index_file}")
    
    def generate_summary_report(self, results: List[Dict]):
        """Generates report resumido"""
        report_file = self.current_export / "reports" / "summary.txt"
        
        lines = []
        lines.append("=" * 80)
        lines.append("RELATÓRIO DE EXPORTAÇÃO - JENKINS")
        lines.append("=" * 80)
        lines.append(f"\nDate: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"Jenkins: {self.jenkins_url}")
        lines.append(f"Total jobs: {len(results)}")
        
        success = [r for r in results if r['status'] == 'success']
        failed = [r for r in results if r['status'] == 'failed']
        
        lines.append(f"\n✓ Exportsdos successfully: {len(success)}")
        lines.append(f"✗ Failures: {len(failed)}")
        
        # Agrupa por tipo
        by_type = {}
        for r in success:
            pipeline_type = r.get('metadata', {}).get('pipeline_type', 'other')
            by_type[pipeline_type] = by_type.get(pipeline_type, 0) + 1
        
        if by_type:
            lines.append("\n📊 Por tipo de pipeline:")
            for ptype, count in sorted(by_type.items()):
                lines.append(f"  • {ptype}: {count}")
        
        # Lists jobs com SCM
        scm_jobs = [r for r in success if r.get('metadata', {}).get('pipeline_type') == 'scm']
        if scm_jobs:
            lines.append(f"\n📁 Jobs com Pipeline from SCM: {len(scm_jobs)}")
            for r in scm_jobs[:10]:  # Primeiros 10
                git_url = r.get('metadata', {}).get('git_url', 'N/A')
                lines.append(f"  • {r['job_name']}")
                lines.append(f"    Git: {git_url}")
        
        if len(scm_jobs) > 10:
            lines.append(f"  ... e mais {len(scm_jobs) - 10} jobs")
        
        # Failures
        if failed:
            lines.append("\n❌ Jobs with export failure:")
            for r in failed:
                lines.append(f"  • {r['job_name']}")
        
        lines.append("\n" + "=" * 80)
        lines.append(f"✓ Configurations exported to: {self.current_export / 'configs'}")
        lines.append("=" * 80)
        
        # Saves e imprime
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        for line in lines:
            print(line)
        
        return report_file


def main():
    parser = argparse.ArgumentParser(
        description='Exports configurations de all jobs do Jenkins',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:

  # Exports todas as configurations
  python jenkins_config_exporter.py \\
      --jenkins-url https://jenkins.empresa.com \\
      --username admin \\
      --token abc123

  # Exports para directory específico
  python jenkins_config_exporter.py \\
      --jenkins-url https://jenkins.empresa.com \\
      --username admin \\
      --token abc123 \\
      --export-dir /backup/jenkins
        """
    )
    
    parser.add_argument('--jenkins-url', required=True, help='URL do Jenkins')
    parser.add_argument('--username', required=True, help='Username do Jenkins')
    parser.add_argument('--token', required=True, help='Token de API')
    parser.add_argument('--export-dir', default='jenkins_exports', 
                       help='Directory para exportação (padrão: jenkins_exports)')
    
    args = parser.parse_args()
    
    try:
        exporter = JenkinsConfigExporter(
            jenkins_url=args.jenkins_url,
            username=args.username,
            token=args.token,
            export_dir=args.export_dir
        )
        
        results = exporter.export_all_configs()
        exporter.generate_summary_report(results)
        
        print("\n🎉 Export completed successfully!")
        
    except KeyboardInterrupt:
        print("\n\n⚠ Operation cancelled")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
