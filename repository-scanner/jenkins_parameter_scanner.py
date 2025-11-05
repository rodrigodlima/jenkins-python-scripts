#!/usr/bin/env python3
"""
Script para buscar parameters no Jenkins (jobs e Jenkinsfiles)
Autor: Generatesdo para busca de ECR_PATH
"""

import requests
import json
import re
import os
import subprocess
from typing import List, Dict, Set
from urllib.parse import urljoin
import argparse
from requests.auth import HTTPBasicAuth


class JenkinsParameterScanner:
    def __init__(self, jenkins_url: str, username: str, token: str):
        """
        Initializes o scanner do Jenkins
        
        Args:
            jenkins_url: URL base do Jenkins (ex: https://jenkins.empresa.com)
            username: Username do Jenkins
            token: Token de API do Jenkins
        """
        self.jenkins_url = jenkins_url.rstrip('/')
        self.auth = HTTPBasicAuth(username, token)
        self.session = requests.Session()
        self.session.auth = self.auth
        
    def get_all_jobs(self, folder_path: str = "") -> List[Dict]:
        """
        Gets all jobs do Jenkins recursively
        """
        jobs = []
        url = f"{self.jenkins_url}/{folder_path}api/json?tree=jobs[name,url,_class,jobs]"
        
        try:
            response = self.session.get(url, verify=True)
            response.raise_for_status()
            data = response.json()
            
            for job in data.get('jobs', []):
                job_class = job.get('_class', '')
                
                # Se for uma pasta, busca recursively
                if 'Folder' in job_class or 'OrganizationFolder' in job_class:
                    sub_jobs = self.get_all_jobs(job['url'].replace(self.jenkins_url, ''))
                    jobs.extend(sub_jobs)
                else:
                    jobs.append(job)
                    
        except Exception as e:
            print(f"Erro ao obter jobs de {folder_path}: {str(e)}")
            
        return jobs
    
    def get_job_config(self, job_url: str) -> str:
        """
        Gets a configuração XML of job
        """
        config_url = f"{job_url}config.xml"
        try:
            response = self.session.get(config_url, verify=True)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Erro ao obter config de {job_url}: {str(e)}")
            return ""
    
    def search_parameter_in_config(self, config_xml: str, parameter_name: str) -> Dict:
        """
        Searches parameter na configuração XML of job
        """
        result = {
            'found_in_parameters': False,
            'found_in_script': False,
            'parameter_type': None,
            'script_matches': []
        }
        
        # Searches na seção de parameters
        param_patterns = [
            rf'<name>{parameter_name}</name>',
            rf'<hudson\.model\.\w+ParameterDefinition>.*?<name>{parameter_name}</name>',
        ]
        
        for pattern in param_patterns:
            if re.search(pattern, config_xml, re.DOTALL):
                result['found_in_parameters'] = True
                # Tenta identificar o tipo
                type_match = re.search(
                    rf'<(hudson\.model\.\w+ParameterDefinition)>.*?<name>{parameter_name}</name>',
                    config_xml, re.DOTALL
                )
                if type_match:
                    result['parameter_type'] = type_match.group(1)
                break
        
        # Searches no script/Jenkinsfile
        script_patterns = [
            rf'\${{?{parameter_name}}}?',
            rf'params\.{parameter_name}',
            rf'env\.{parameter_name}',
            rf'{parameter_name}\s*=',
        ]
        
        for pattern in script_patterns:
            matches = re.finditer(pattern, config_xml)
            for match in matches:
                result['found_in_script'] = True
                # Extracts contexto ao redor
                start = max(0, match.start() - 50)
                end = min(len(config_xml), match.end() + 50)
                context = config_xml[start:end].replace('\n', ' ')
                result['script_matches'].append(context)
        
        return result
    
    def scan_jobs(self, parameter_name: str) -> List[Dict]:
        """
        Escaneia all jobs procurando pelo parameter
        """
        print(f"Searchesndo parameter '{parameter_name}' no Jenkins...")
        print(f"URL: {self.jenkins_url}")
        print("-" * 80)
        
        all_jobs = self.get_all_jobs()
        print(f"\nTotal de jobs encontrados: {len(all_jobs)}")
        print("-" * 80)
        
        results = []
        
        for idx, job in enumerate(all_jobs, 1):
            job_name = job.get('name')
            job_url = job.get('url')
            
            print(f"\n[{idx}/{len(all_jobs)}] Analyzesndo: {job_name}")
            
            config = self.get_job_config(job_url)
            if not config:
                continue
            
            search_result = self.search_parameter_in_config(config, parameter_name)
            
            if search_result['found_in_parameters'] or search_result['found_in_script']:
                result_entry = {
                    'job_name': job_name,
                    'job_url': job_url,
                    'job_class': job.get('_class', ''),
                    **search_result
                }
                results.append(result_entry)
                
                print(f"  ✓ ENCONTRADO!")
                if search_result['found_in_parameters']:
                    print(f"    - Definido como parameter ({search_result['parameter_type']})")
                if search_result['found_in_script']:
                    print(f"    - Usado no script ({len(search_result['script_matches'])} ocorrências)")
        
        return results
    
    def generate_report(self, results: List[Dict], parameter_name: str, output_file: str = None):
        """
        Generates report dos resultados
        """
        print("\n" + "=" * 80)
        print(f"RELATÓRIO: Searches por '{parameter_name}'")
        print("=" * 80)
        
        report_lines = []
        report_lines.append(f"Total de jobs com o parameter: {len(results)}\n")
        
        if not results:
            report_lines.append("Nenhum job encontrado com este parameter.")
            print(report_lines[-1])
            return
        
        # Agrupa por tipo
        with_parameters = [r for r in results if r['found_in_parameters']]
        with_script_only = [r for r in results if r['found_in_script'] and not r['found_in_parameters']]
        
        report_lines.append(f"\nJobs com parameter definido: {len(with_parameters)}")
        report_lines.append(f"Jobs usando apenas no script: {len(with_script_only)}\n")
        
        report_lines.append("\n" + "-" * 80)
        report_lines.append("JOBS COM PARÂMETRO DEFINIDO:")
        report_lines.append("-" * 80)
        
        for result in with_parameters:
            report_lines.append(f"\n• {result['job_name']}")
            report_lines.append(f"  URL: {result['job_url']}")
            report_lines.append(f"  Tipo: {result['parameter_type'] or 'N/A'}")
            if result['script_matches']:
                report_lines.append(f"  Usages no script: {len(result['script_matches'])}")
        
        report_lines.append("\n" + "-" * 80)
        report_lines.append("JOBS USANDO APENAS NO SCRIPT:")
        report_lines.append("-" * 80)
        
        for result in with_script_only:
            report_lines.append(f"\n• {result['job_name']}")
            report_lines.append(f"  URL: {result['job_url']}")
            report_lines.append(f"  Occurrences: {len(result['script_matches'])}")
            
            # Mostra alguns exemplos de uso
            for i, match in enumerate(result['script_matches'][:3], 1):
                report_lines.append(f"  Exemplo {i}: ...{match}...")
        
        # Prints o report
        for line in report_lines:
            print(line)
        
        # Saves to file se especificado
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_lines))
            print(f"\n✓ Report salvo em: {output_file}")
        
        # Saves JSON detalhado
        json_file = output_file.replace('.txt', '.json') if output_file else 'jenkins_scan_results.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"✓ Resultados detalhados salvos em: {json_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Searches parameters em jobs do Jenkins e Jenkinsfiles'
    )
    parser.add_argument(
        '--jenkins-url',
        required=True,
        help='URL do Jenkins (ex: https://jenkins.empresa.com)'
    )
    parser.add_argument(
        '--username',
        required=True,
        help='Username do Jenkins'
    )
    parser.add_argument(
        '--token',
        required=True,
        help='Token de API do Jenkins'
    )
    parser.add_argument(
        '--parameter',
        default='ECR_PATH',
        help='Nome do parameter a buscar (padrão: ECR_PATH)'
    )
    parser.add_argument(
        '--output',
        default='jenkins_parameter_report.txt',
        help='Arquivo de saída para o report (padrão: jenkins_parameter_report.txt)'
    )
    
    args = parser.parse_args()
    
    try:
        scanner = JenkinsParameterScanner(
            jenkins_url=args.jenkins_url,
            username=args.username,
            token=args.token
        )
        
        results = scanner.scan_jobs(args.parameter)
        scanner.generate_report(results, args.parameter, args.output)
        
    except KeyboardInterrupt:
        print("\n\nOperação cancelada pelo usuário.")
    except Exception as e:
        print(f"\n✗ Erro: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
