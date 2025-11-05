#!/usr/bin/env python3
"""
Script unificado para buscar parameters no Jenkins e nos repositórios Git
Combina resultados de ambas as fontes em um report consolidado
"""

import argparse
import sys
from pathlib import Path

# Importa os scanners (assumindo que estão no mesmo diretório)
from jenkins_parameter_scanner import JenkinsParameterScanner
from git_repository_scanner import GitRepositoryScanner


class UnifiedScanner:
    def __init__(self, jenkins_url: str, username: str, token: str, repos_path: str = None):
        """
        Initializes o scanner unificado
        """
        self.jenkins_scanner = JenkinsParameterScanner(jenkins_url, username, token)
        self.git_scanner = GitRepositoryScanner(repos_path) if repos_path else None
        
    def scan_all(self, parameter_name: str) -> dict:
        """
        Executa scan completo em Jenkins e repositórios Git
        """
        results = {
            'parameter_name': parameter_name,
            'jenkins_results': [],
            'git_results': []
        }
        
        # Scan do Jenkins
        print("=" * 80)
        print("FASE 1: SCAN DO JENKINS")
        print("=" * 80)
        results['jenkins_results'] = self.jenkins_scanner.scan_jobs(parameter_name)
        
        # Scan dos repositórios Git
        if self.git_scanner:
            print("\n" + "=" * 80)
            print("FASE 2: SCAN DOS REPOSITÓRIOS GIT")
            print("=" * 80)
            results['git_results'] = self.git_scanner.scan_repositories(parameter_name)
        
        return results
    
    def generate_unified_report(self, results: dict, output_file: str = None):
        """
        Generates report consolidado
        """
        parameter_name = results['parameter_name']
        jenkins_results = results['jenkins_results']
        git_results = results['git_results']
        
        print("\n" + "=" * 80)
        print(f"RELATÓRIO CONSOLIDADO: '{parameter_name}'")
        print("=" * 80)
        
        report_lines = []
        
        # Summary executivo
        report_lines.append("\n📊 RESUMO EXECUTIVO")
        report_lines.append("-" * 80)
        report_lines.append(f"Parâmetro buscado: {parameter_name}")
        report_lines.append(f"Jobs Jenkins encontrados: {len(jenkins_results)}")
        report_lines.append(f"Repositórios Git encontrados: {len(git_results)}")
        
        jenkins_with_param = len([r for r in jenkins_results if r.get('found_in_parameters')])
        jenkins_script_only = len([r for r in jenkins_results if r.get('found_in_script') and not r.get('found_in_parameters')])
        
        report_lines.append(f"\nDetalhamento Jenkins:")
        report_lines.append(f"  - Com parameter definido: {jenkins_with_param}")
        report_lines.append(f"  - Usado apenas no script: {jenkins_script_only}")
        
        if git_results:
            total_git_matches = sum(len(r['matches']) for r in git_results)
            report_lines.append(f"\nDetalhamento Git:")
            report_lines.append(f"  - Total de arquivos com ocorrências: {total_git_matches}")
        
        # Análise cruzada
        report_lines.append("\n\n🔍 ANÁLISE CRUZADA")
        report_lines.append("-" * 80)
        
        # Creates um conjunto de repositórios encontrados no Git
        git_repo_names = {r['repo_name'] for r in git_results} if git_results else set()
        
        # Checks se os jobs do Jenkins correspondem aos repositórios
        for jenkins_job in jenkins_results:
            job_name = jenkins_job['job_name']
            
            # Tenta encontrar correspondência com repositórios
            matching_repos = [repo for repo in git_repo_names if repo.lower() in job_name.lower() or job_name.lower() in repo.lower()]
            
            if matching_repos:
                report_lines.append(f"\n✓ Job '{job_name}' tem correspondência com repo(s): {', '.join(matching_repos)}")
            else:
                report_lines.append(f"\n⚠ Job '{job_name}' sem correspondência clara nos repositórios escaneados")
        
        # Repositórios sem jobs correspondentes
        jenkins_job_names = {j['job_name'].lower() for j in jenkins_results}
        orphan_repos = []
        
        for repo in git_repo_names:
            has_match = any(repo.lower() in job_name or job_name in repo.lower() for job_name in jenkins_job_names)
            if not has_match:
                orphan_repos.append(repo)
        
        if orphan_repos:
            report_lines.append(f"\n\n⚠ Repositórios com '{parameter_name}' mas sem job Jenkins correspondente:")
            for repo in orphan_repos:
                report_lines.append(f"  - {repo}")
        
        # Recomendações
        report_lines.append("\n\n💡 RECOMENDAÇÕES")
        report_lines.append("-" * 80)
        
        if jenkins_script_only > 0:
            report_lines.append(f"• {jenkins_script_only} job(s) usam '{parameter_name}' no script mas não o definem como parameter")
            report_lines.append("  Considere parametrizar esses valores para maior flexibilidade")
        
        if orphan_repos:
            report_lines.append(f"\n• {len(orphan_repos)} repositório(s) referenciam '{parameter_name}' mas não têm job Jenkins correspondente")
            report_lines.append("  Verifique se esses repositórios precisam de pipelines configurados")
        
        if not git_results and jenkins_results:
            report_lines.append("\n• Scan de repositórios Git não foi executado")
            report_lines.append("  Execute com --repos-path para análise completa")
        
        # Prints o report
        for line in report_lines:
            print(line)
        
        # Chama os reports individuais
        print("\n\n" + "=" * 80)
        print("DETALHES - JENKINS")
        print("=" * 80)
        self.jenkins_scanner.generate_report(jenkins_results, parameter_name, None)
        
        if git_results:
            print("\n\n" + "=" * 80)
            print("DETALHES - REPOSITÓRIOS GIT")
            print("=" * 80)
            self.git_scanner.generate_report(git_results, parameter_name, None)
        
        # Saves report consolidado
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write('\n'.join(report_lines))
            print(f"\n✓ Report consolidado salvo em: {output_file}")
        
        # Saves JSON consolidado
        import json
        json_file = output_file.replace('.txt', '.json') if output_file else 'unified_scan_results.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"✓ Resultados completos salvos em: {json_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Searches unificada de parameters no Jenkins e repositórios Git',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples de uso:

  # Searches apenas no Jenkins:
  python unified_scanner.py --jenkins-url https://jenkins.empresa.com \\
      --username seu_user --token seu_token --parameter ECR_PATH

  # Searches no Jenkins e nos repositórios Git:
  python unified_scanner.py --jenkins-url https://jenkins.empresa.com \\
      --username seu_user --token seu_token \\
      --repos-path /caminho/para/repos --parameter ECR_PATH
        """
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
        '--repos-path',
        help='Caminho base onde estão os repositórios Git (opcional)'
    )
    parser.add_argument(
        '--parameter',
        default='ECR_PATH',
        help='Nome do parameter a buscar (padrão: ECR_PATH)'
    )
    parser.add_argument(
        '--output',
        default='unified_parameter_report.txt',
        help='Arquivo de saída para o report consolidado'
    )
    
    args = parser.parse_args()
    
    try:
        scanner = UnifiedScanner(
            jenkins_url=args.jenkins_url,
            username=args.username,
            token=args.token,
            repos_path=args.repos_path
        )
        
        results = scanner.scan_all(args.parameter)
        scanner.generate_unified_report(results, args.output)
        
        print("\n" + "=" * 80)
        print("✓ SCAN COMPLETO!")
        print("=" * 80)
        
    except KeyboardInterrupt:
        print("\n\nOperação cancelada pelo usuário.")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Erro: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
