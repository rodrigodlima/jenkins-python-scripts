#!/usr/bin/env python3
"""
Scanner Jenkins Melhorado - Versão 2.0
Suporta diferentes tipos de pipeline e busca inteligente
"""

import requests
import json
import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
from requests.auth import HTTPBasicAuth
import argparse
import subprocess
from pathlib import Path


class EnhancedJenkinsScanner:
    def __init__(self, jenkins_url: str, username: str, token: str, git_repos_path: str = None):
        """
        Scanner Jenkins melhorado
        
        Args:
            jenkins_url: URL base do Jenkins
            username: Username do Jenkins
            token: Token de API
            git_repos_path: Path opcional para repositórios Git clonados
        """
        self.jenkins_url = jenkins_url.rstrip('/')
        self.auth = HTTPBasicAuth(username, token)
        self.session = requests.Session()
        self.session.auth = self.auth
        self.git_repos_path = Path(git_repos_path) if git_repos_path else None
        
    def get_all_jobs(self, folder_path: str = "") -> List[Dict]:
        """Gets all jobs do Jenkins recursively"""
        jobs = []
        url = f"{self.jenkins_url}/{folder_path}api/json?tree=jobs[name,url,_class,jobs]"
        
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
            print(f"Error getting jobs de {folder_path}: {str(e)}")
            
        return jobs
    
    def get_job_config(self, job_url: str) -> str:
        """Gets a configuration XML of job"""
        config_url = f"{job_url}config.xml"
        try:
            response = self.session.get(config_url, verify=True)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"  ⚠ Error getting config de {job_url}: {str(e)}")
            return ""
    
    def analyze_job_type(self, config_xml: str) -> Dict:
        """
        Analyzes o tipo de job e extrai informações relevantes
        """
        job_info = {
            'type': 'unknown',
            'has_inline_script': False,
            'scm_type': None,
            'git_url': None,
            'jenkinsfile_path': None,
            'inline_script': None
        }
        
        try:
            root = ET.fromstring(config_xml)
            
            # Detects tipo de job
            if root.tag == 'flow-definition':
                job_info['type'] = 'pipeline'
                
                # Checks se é Pipeline Script (inline)
                definition = root.find('.//definition')
                if definition is not None:
                    definition_class = definition.get('class', '')
                    
                    if 'CpsFlowDefinition' in definition_class:
                        job_info['has_inline_script'] = True
                        script_elem = definition.find('script')
                        if script_elem is not None:
                            job_info['inline_script'] = script_elem.text
                    
                    elif 'CpsScmFlowDefinition' in definition_class:
                        job_info['scm_type'] = 'scm'
                        
                        # Extracts informações do SCM
                        scm = definition.find('.//scm')
                        if scm is not None:
                            # Git URL
                            url_elem = scm.find('.//url')
                            if url_elem is not None:
                                job_info['git_url'] = url_elem.text
                        
                        # Path do Jenkinsfile
                        script_path = definition.find('.//scriptPath')
                        if script_path is not None:
                            job_info['jenkinsfile_path'] = script_path.text
            
            elif root.tag in ['project', 'maven2-moduleset']:
                job_info['type'] = 'freestyle'
                
        except ET.ParseErrorr as e:
            print(f"  ⚠ Error ao parsear XML: {str(e)}")
        
        return job_info
    
    def get_jenkinsfile_from_git(self, git_url: str, jenkinsfile_path: str = 'Jenkinsfile') -> Optional[str]:
        """
        Tenta obter o Jenkinsfile do repositório Git local
        """
        if not self.git_repos_path or not self.git_repos_path.exists():
            return None
        
        # Extracts o nome do repositório da URL
        # Ex: https://github.com/empresa/repo.git -> repo
        repo_name = git_url.rstrip('/').split('/')[-1].replace('.git', '')
        
        # Searches o repositório localmente
        possible_paths = [
            self.git_repos_path / repo_name / jenkinsfile_path,
            self.git_repos_path / repo_name.lower() / jenkinsfile_path,
        ]
        
        for path in possible_paths:
            if path.exists():
                try:
                    with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                        return f.read()
                except Exception as e:
                    print(f"  ⚠ Error ao ler {path}: {str(e)}")
        
        return None
    
    def search_parameter_in_text(self, text: str, parameter_name: str) -> Dict:
        """
        Searches parameter em texto (script, Jenkinsfile, etc)
        """
        result = {
            'found': False,
            'matches': [],
            'has_parameters_block': False,
            'defined_as_parameter': False
        }
        
        if not text:
            return result
        
        # Checks se tem bloco parameters
        if re.search(r'parameters\s*{', text):
            result['has_parameters_block'] = True
        
        # Checks se o parameter é definido
        param_definition_patterns = [
            rf'string\s*\(\s*name\s*:\s*[\'\"]{parameter_name}[\'\"]',
            rf'booleanParam\s*\(\s*name\s*:\s*[\'\"]{parameter_name}[\'\"]',
            rf'choice\s*\(\s*name\s*:\s*[\'\"]{parameter_name}[\'\"]',
            rf'password\s*\(\s*name\s*:\s*[\'\"]{parameter_name}[\'\"]',
        ]
        
        for pattern in param_definition_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                result['defined_as_parameter'] = True
                break
        
        # Searches usos do parameter
        usage_patterns = [
            rf'\${{?{parameter_name}}}?',
            rf'params\.{parameter_name}',
            rf'env\.{parameter_name}',
            rf'{parameter_name}\s*=',
        ]
        
        for pattern in usage_patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                result['found'] = True
                # Extracts contexto
                start = max(0, match.start() - 80)
                end = min(len(text), match.end() + 80)
                context = text[start:end].replace('\n', ' ').strip()
                result['matches'].append({
                    'pattern': pattern,
                    'context': context,
                    'position': match.start()
                })
        
        return result
    
    def analyze_job(self, job: Dict, parameter_name: str) -> Dict:
        """
        Análise completa de um job
        """
        job_name = job.get('name')
        job_url = job.get('url')
        
        result = {
            'job_name': job_name,
            'job_url': job_url,
            'job_class': job.get('_class', ''),
            'found': False,
            'sources': []  # List of onde o parameter foi encontrado
        }
        
        print(f"  Analyzesndo: {job_name}")
        
        # 1. Gets configuration of job
        config_xml = self.get_job_config(job_url)
        if not config_xml:
            return result
        
        # 2. Analyzes tipo de job
        job_info = self.analyze_job_type(config_xml)
        result['job_type'] = job_info['type']
        
        # 3. Searches em parameters definidos in XML
        xml_param_search = self.search_parameter_in_xml(config_xml, parameter_name)
        if xml_param_search['found_in_parameters']:
            result['found'] = True
            result['sources'].append({
                'location': 'job_parameters',
                'type': 'definition',
                'parameter_type': xml_param_search.get('parameter_type')
            })
            print(f"    ✓ Found em: Parameters do Job")
        
        # 4. Se tem script inline, busca nele
        if job_info['has_inline_script'] and job_info['inline_script']:
            script_search = self.search_parameter_in_text(
                job_info['inline_script'], 
                parameter_name
            )
            if script_search['found']:
                result['found'] = True
                result['sources'].append({
                    'location': 'inline_script',
                    'type': 'usage',
                    'matches': len(script_search['matches']),
                    'defined_in_script': script_search['defined_as_parameter']
                })
                print(f"    ✓ Found em: Script Inline ({len(script_search['matches'])} usos)")
        
        # 5. Se usa SCM, tenta buscar o Jenkinsfile
        elif job_info['scm_type'] == 'scm' and job_info['git_url']:
            result['git_url'] = job_info['git_url']
            result['jenkinsfile_path'] = job_info['jenkinsfile_path'] or 'Jenkinsfile'
            
            jenkinsfile_content = self.get_jenkinsfile_from_git(
                job_info['git_url'],
                result['jenkinsfile_path']
            )
            
            if jenkinsfile_content:
                jenkinsfile_search = self.search_parameter_in_text(
                    jenkinsfile_content,
                    parameter_name
                )
                if jenkinsfile_search['found']:
                    result['found'] = True
                    result['sources'].append({
                        'location': 'jenkinsfile_from_git',
                        'type': 'usage' if not jenkinsfile_search['defined_as_parameter'] else 'definition_and_usage',
                        'matches': len(jenkinsfile_search['matches']),
                        'defined_in_jenkinsfile': jenkinsfile_search['defined_as_parameter'],
                        'git_url': job_info['git_url'],
                        'file_path': result['jenkinsfile_path']
                    })
                    print(f"    ✓ Found em: Jenkinsfile do Git ({len(jenkinsfile_search['matches'])} usos)")
            else:
                # Jenkinsfile não encontrado localmente
                result['sources'].append({
                    'location': 'jenkinsfile_not_found',
                    'note': 'Jenkinsfile não encontrado nos repos locais',
                    'git_url': job_info['git_url'],
                    'file_path': result['jenkinsfile_path']
                })
                print(f"    ⚠ Jenkinsfile não encontrado localmente")
                print(f"      Git: {job_info['git_url']}")
                print(f"      Path: {result['jenkinsfile_path']}")
        
        # 6. Searches também in XML completo (pode ter em outros lugares)
        if xml_param_search['found_in_script']:
            if not any(s['location'] in ['inline_script', 'jenkinsfile_from_git'] for s in result['sources']):
                result['found'] = True
                result['sources'].append({
                    'location': 'xml_script',
                    'type': 'usage',
                    'matches': len(xml_param_search['script_matches'])
                })
                print(f"    ✓ Found em: Script in XML")
        
        return result
    
    def search_parameter_in_xml(self, config_xml: str, parameter_name: str) -> Dict:
        """Searches parameter na configuration XML"""
        result = {
            'found_in_parameters': False,
            'found_in_script': False,
            'parameter_type': None,
            'script_matches': []
        }
        
        # Searches em parameters
        param_patterns = [
            rf'<name>{parameter_name}</name>',
            rf'<hudson\.model\.\w+ParameterDefinition>.*?<name>{parameter_name}</name>',
        ]
        
        for pattern in param_patterns:
            if re.search(pattern, config_xml, re.DOTALL):
                result['found_in_parameters'] = True
                type_match = re.search(
                    rf'<(hudson\.model\.\w+ParameterDefinition)>.*?<name>{parameter_name}</name>',
                    config_xml, re.DOTALL
                )
                if type_match:
                    result['parameter_type'] = type_match.group(1)
                break
        
        # Searches em scripts
        script_patterns = [
            rf'\${{?{parameter_name}}}?',
            rf'params\.{parameter_name}',
            rf'env\.{parameter_name}',
        ]
        
        for pattern in script_patterns:
            matches = re.finditer(pattern, config_xml)
            for match in matches:
                result['found_in_script'] = True
                start = max(0, match.start() - 50)
                end = min(len(config_xml), match.end() + 50)
                context = config_xml[start:end].replace('\n', ' ')
                result['script_matches'].append(context)
        
        return result
    
    def scan_all_jobs(self, parameter_name: str) -> List[Dict]:
        """Escaneia all jobs"""
        print(f"🔍 Searchesndo '{parameter_name}' em all jobs do Jenkins")
        print(f"Jenkins: {self.jenkins_url}")
        if self.git_repos_path:
            print(f"Repos Git: {self.git_repos_path}")
        print("-" * 80)
        
        all_jobs = self.get_all_jobs()
        print(f"\n📊 Total jobs encontrados: {len(all_jobs)}")
        print("-" * 80)
        
        results = []
        
        for idx, job in enumerate(all_jobs, 1):
            print(f"\n[{idx}/{len(all_jobs)}]", end=" ")
            
            result = self.analyze_job(job, parameter_name)
            
            if result['found']:
                results.append(result)
        
        return results
    
    def generate_enhanced_report(self, results: List[Dict], parameter_name: str, output_file: str = None):
        """Generates report melhorado"""
        print("\n" + "=" * 80)
        print(f"📊 RELATÓRIO DETALHADO: '{parameter_name}'")
        print("=" * 80)
        
        report_lines = []
        
        # Summary
        report_lines.append(f"\nTotal jobs com '{parameter_name}': {len(results)}")
        
        # Agrupa por localização
        by_location = {}
        for result in results:
            for source in result['sources']:
                loc = source['location']
                by_location[loc] = by_location.get(loc, 0) + 1
        
        report_lines.append("\n📍 Localizações onde o parameter foi encontrado:")
        for loc, count in sorted(by_location.items(), key=lambda x: x[1], reverse=True):
            loc_names = {
                'job_parameters': 'Parameters do Job',
                'inline_script': 'Script Inline (Pipeline)',
                'jenkinsfile_from_git': 'Jenkinsfile (do Git)',
                'xml_script': 'Script in XML',
                'jenkinsfile_not_found': 'Jenkinsfile não encontrado localmente'
            }
            report_lines.append(f"  • {loc_names.get(loc, loc)}: {count} job(s)")
        
        # Details por job
        report_lines.append("\n" + "=" * 80)
        report_lines.append("DETALHES POR JOB")
        report_lines.append("=" * 80)
        
        for result in results:
            report_lines.append(f"\n{'─' * 80}")
            report_lines.append(f"📋 Job: {result['job_name']}")
            report_lines.append(f"   URL: {result['job_url']}")
            report_lines.append(f"   Tipo: {result.get('job_type', 'unknown')}")
            
            if result.get('git_url'):
                report_lines.append(f"   Git: {result['git_url']}")
                report_lines.append(f"   Jenkinsfile: {result.get('jenkinsfile_path', 'Jenkinsfile')}")
            
            report_lines.append(f"\n   🔍 Parâmetro encontrado em:")
            for source in result['sources']:
                loc = source['location']
                if loc == 'job_parameters':
                    report_lines.append(f"      ✓ Parameters do Job (tipo: {source.get('parameter_type', 'N/A')})")
                elif loc == 'inline_script':
                    defined = " [DEFINIDO NO SCRIPT]" if source.get('defined_in_script') else ""
                    report_lines.append(f"      ✓ Script Inline - {source.get('matches', 0)} uso(s){defined}")
                elif loc == 'jenkinsfile_from_git':
                    defined = " [DEFINIDO NO JENKINSFILE]" if source.get('defined_in_jenkinsfile') else ""
                    report_lines.append(f"      ✓ Jenkinsfile (Git) - {source.get('matches', 0)} uso(s){defined}")
                elif loc == 'jenkinsfile_not_found':
                    report_lines.append(f"      ⚠ Jenkinsfile não encontrado localmente")
                    report_lines.append(f"        (Git: {source.get('git_url')})")
                elif loc == 'xml_script':
                    report_lines.append(f"      ✓ Script in XML - {source.get('matches', 0)} uso(s)")
        
        # Recomendações
        report_lines.append("\n" + "=" * 80)
        report_lines.append("💡 RECOMENDAÇÕES")
        report_lines.append("=" * 80)
        
        jenkinsfiles_not_found = sum(
            1 for r in results 
            if any(s['location'] == 'jenkinsfile_not_found' for s in r['sources'])
        )
        
        if jenkinsfiles_not_found > 0:
            report_lines.append(f"\n⚠ {jenkinsfiles_not_found} job(s) usam Jenkinsfile do Git que não foi encontrado localmente")
            report_lines.append("  Sugestões:")
            report_lines.append("  1. Clone os repositórios faltantes")
            report_lines.append("  2. Execute o scanner Git separadamente")
            report_lines.append("  3. Forneça o path correto com --git-repos-path")
        
        # Prints
        for line in report_lines:
            print(line)
        
        # Saves
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_lines))
            print(f"\n✓ Report salvo em: {output_file}")
        
        json_file = output_file.replace('.txt', '.json') if output_file else 'enhanced_scan_results.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"✓ Detailed JSON saved to: {json_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Scanner Jenkins Melhorado - Searches em jobs e Jenkinsfiles do Git',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:

  # Searches apenas no Jenkins (sem acesso aos repos Git):
  python enhanced_jenkins_scanner.py \\
      --jenkins-url https://jenkins.empresa.com \\
      --username user --token token \\
      --parameter ECR_PATH

  # Searches no Jenkins + Jenkinsfiles locais (RECOMENDADO):
  python enhanced_jenkins_scanner.py \\
      --jenkins-url https://jenkins.empresa.com \\
      --username user --token token \\
      --git-repos-path ~/projetos \\
      --parameter ECR_PATH
        """
    )
    
    parser.add_argument('--jenkins-url', required=True, help='URL do Jenkins')
    parser.add_argument('--username', required=True, help='Username do Jenkins')
    parser.add_argument('--token', required=True, help='Token de API')
    parser.add_argument('--git-repos-path', help='Path para repos Git clonados (opcional mas recomendado)')
    parser.add_argument('--parameter', default='ECR_PATH', help='Parâmetro a buscar')
    parser.add_argument('--output', default='enhanced_jenkins_report.txt', help='File de saída')
    
    args = parser.parse_args()
    
    try:
        scanner = EnhancedJenkinsScanner(
            jenkins_url=args.jenkins_url,
            username=args.username,
            token=args.token,
            git_repos_path=args.git_repos_path
        )
        
        results = scanner.scan_all_jobs(args.parameter)
        scanner.generate_enhanced_report(results, args.parameter, args.output)
        
        print("\n" + "=" * 80)
        print("✅ SCAN COMPLETO!")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\n⚠ Operation cancelled")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
