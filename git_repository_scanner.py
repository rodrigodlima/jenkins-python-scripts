#!/usr/bin/env python3
"""
Script para buscar parameters em Jenkinsfiles nos repositórios Git
"""

import os
import subprocess
import re
import json
from pathlib import Path
from typing import List, Dict, Set
import argparse


class GitRepositoryScanner:
    def __init__(self, repos_path: str):
        """
        Initializes o scanner de repositórios Git
        
        Args:
            repos_path: Caminho base onde estão os repositórios
        """
        self.repos_path = Path(repos_path)
        
    def find_git_repositories(self) -> List[Path]:
        """
        Encontra todos os repositórios Git no diretório base
        """
        repos = []
        
        if not self.repos_path.exists():
            print(f"✗ Caminho não existe: {self.repos_path}")
            return repos
        
        print(f"Searchesndo repositórios Git em: {self.repos_path}")
        
        # Searches por diretórios .git
        for root, dirs, files in os.walk(self.repos_path):
            if '.git' in dirs:
                repo_path = Path(root)
                repos.append(repo_path)
                # Não precisa entrar em subdiretórios de um repositório
                dirs.clear()
        
        print(f"Encontrados {len(repos)} repositórios Git")
        return repos
    
    def search_in_repository(self, repo_path: Path, parameter_name: str) -> Dict:
        """
        Searches o parameter em um repositório específico
        """
        result = {
            'repo_name': repo_path.name,
            'repo_path': str(repo_path),
            'matches': []
        }
        
        try:
            # Uses git grep para buscar o parameter
            cmd = [
                'git', 'grep', '-n', '-i',
                parameter_name,
                '--', 'Jenkinsfile*', '*.groovy', '*.gradle'
            ]
            
            process = subprocess.run(
                cmd,
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if process.returncode == 0:
                lines = process.stdout.strip().split('\n')
                
                for line in lines:
                    if not line:
                        continue
                    
                    # Parse: filename:line_number:content
                    parts = line.split(':', 2)
                    if len(parts) >= 3:
                        match_info = {
                            'file': parts[0],
                            'line': parts[1],
                            'content': parts[2].strip()
                        }
                        result['matches'].append(match_info)
            
        except subprocess.TimeoutExpired:
            print(f"  ⚠ Timeout ao buscar em {repo_path.name}")
        except Exception as e:
            print(f"  ✗ Erro ao buscar em {repo_path.name}: {str(e)}")
        
        return result if result['matches'] else None
    
    def analyze_jenkinsfile(self, repo_path: Path, file_path: str) -> Dict:
        """
        Analyzes um Jenkinsfile específico para contexto adicional
        """
        full_path = repo_path / file_path
        
        analysis = {
            'has_parameters_block': False,
            'has_properties_block': False,
            'parameter_definitions': [],
            'usage_contexts': []
        }
        
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Checks blocos de parameters
            if re.search(r'parameters\s*{', content):
                analysis['has_parameters_block'] = True
            
            if re.search(r'properties\s*\(\s*\[.*?parameters', content, re.DOTALL):
                analysis['has_properties_block'] = True
            
            # Searches definições de parameters
            param_patterns = [
                r'string\s*\(\s*name\s*:\s*[\'"](\w+)[\'"]',
                r'booleanParam\s*\(\s*name\s*:\s*[\'"](\w+)[\'"]',
                r'choice\s*\(\s*name\s*:\s*[\'"](\w+)[\'"]',
            ]
            
            for pattern in param_patterns:
                matches = re.finditer(pattern, content)
                for match in matches:
                    analysis['parameter_definitions'].append(match.group(1))
            
        except Exception as e:
            print(f"  ⚠ Erro ao analisar {file_path}: {str(e)}")
        
        return analysis
    
    def scan_repositories(self, parameter_name: str) -> List[Dict]:
        """
        Escaneia todos os repositórios procurando pelo parameter
        """
        repos = self.find_git_repositories()
        
        if not repos:
            print("Nenhum repositório Git encontrado.")
            return []
        
        print(f"\nSearchesndo '{parameter_name}' nos repositórios...")
        print("-" * 80)
        
        results = []
        
        for idx, repo_path in enumerate(repos, 1):
            print(f"\n[{idx}/{len(repos)}] {repo_path.name}")
            
            result = self.search_in_repository(repo_path, parameter_name)
            
            if result:
                # Adds análise contextual for each arquivo
                for match in result['matches']:
                    analysis = self.analyze_jenkinsfile(repo_path, match['file'])
                    match['analysis'] = analysis
                
                results.append(result)
                print(f"  ✓ {len(result['matches'])} ocorrência(s) encontrada(s)")
            
        return results
    
    def generate_report(self, results: List[Dict], parameter_name: str, output_file: str = None):
        """
        Generates report dos resultados
        """
        print("\n" + "=" * 80)
        print(f"RELATÓRIO: Searches em Repositórios Git por '{parameter_name}'")
        print("=" * 80)
        
        report_lines = []
        report_lines.append(f"Total de repositórios com o parameter: {len(results)}\n")
        
        if not results:
            report_lines.append("Nenhum repositório encontrado com este parameter.")
            print(report_lines[-1])
            return
        
        total_matches = sum(len(r['matches']) for r in results)
        report_lines.append(f"Total de ocorrências: {total_matches}\n")
        
        for result in results:
            report_lines.append("\n" + "-" * 80)
            report_lines.append(f"REPOSITÓRIO: {result['repo_name']}")
            report_lines.append(f"Caminho: {result['repo_path']}")
            report_lines.append(f"Occurrences: {len(result['matches'])}")
            report_lines.append("-" * 80)
            
            for match in result['matches']:
                report_lines.append(f"\n  📄 Arquivo: {match['file']}")
                report_lines.append(f"     Linha: {match['line']}")
                report_lines.append(f"     Conteúdo: {match['content']}")
                
                analysis = match.get('analysis', {})
                if analysis.get('has_parameters_block'):
                    report_lines.append(f"     ℹ️  Tem bloco 'parameters'")
                if analysis.get('parameter_definitions'):
                    params = ', '.join(analysis['parameter_definitions'][:5])
                    report_lines.append(f"     ℹ️  Parâmetros definidos: {params}")
        
        # Prints o report
        for line in report_lines:
            print(line)
        
        # Saves to file
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_lines))
            print(f"\n✓ Report salvo em: {output_file}")
        
        # Saves JSON
        json_file = output_file.replace('.txt', '.json') if output_file else 'git_scan_results.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"✓ Resultados detalhados salvos em: {json_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Searches parameters em Jenkinsfiles nos repositórios Git'
    )
    parser.add_argument(
        '--repos-path',
        required=True,
        help='Caminho base onde estão os repositórios Git'
    )
    parser.add_argument(
        '--parameter',
        default='ECR_PATH',
        help='Nome do parameter a buscar (padrão: ECR_PATH)'
    )
    parser.add_argument(
        '--output',
        default='git_parameter_report.txt',
        help='Arquivo de saída para o report'
    )
    
    args = parser.parse_args()
    
    try:
        scanner = GitRepositoryScanner(args.repos_path)
        results = scanner.scan_repositories(args.parameter)
        scanner.generate_report(results, args.parameter, args.output)
        
    except KeyboardInterrupt:
        print("\n\nOperação cancelada pelo usuário.")
    except Exception as e:
        print(f"\n✗ Erro: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
