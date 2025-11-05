#!/bin/bash
###############################################################################
# Script auxiliar para executar o scanner de parâmetros Jenkins/Git
# Facilita a execução sem precisar passar todos os argumentos
###############################################################################

set -e

# Cores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Função para exibir banner
show_banner() {
    echo -e "${BLUE}"
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║        Jenkins & Git Parameter Scanner                     ║"
    echo "║        Busca automatizada de parâmetros                    ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
}

# Função para exibir menu
show_menu() {
    echo -e "${GREEN}Escolha o tipo de scan:${NC}"
    echo "1) Scan Completo (Jenkins + Git)"
    echo "2) Apenas Jenkins"
    echo "3) Apenas Repositórios Git"
    echo "4) Múltiplos Parâmetros (Jenkins + Git)"
    echo "5) Configurar credenciais"
    echo "6) Sair"
    echo
}

# Função para ler configurações
read_config() {
    if [ -f "config.ini" ]; then
        JENKINS_URL=$(grep "^url" config.ini | cut -d'=' -f2 | tr -d ' ')
        JENKINS_USER=$(grep "^username" config.ini | cut -d'=' -f2 | tr -d ' ')
        JENKINS_TOKEN=$(grep "^token" config.ini | cut -d'=' -f2 | tr -d ' ')
        REPOS_PATH=$(grep "^repos_path" config.ini | cut -d'=' -f2 | tr -d ' ')
        DEFAULT_PARAM=$(grep "^default_parameter" config.ini | cut -d'=' -f2 | tr -d ' ')
        return 0
    else
        return 1
    fi
}

# Função para configurar credenciais
configure() {
    echo -e "${YELLOW}Configuração das credenciais${NC}"
    echo
    
    read -p "URL do Jenkins (ex: https://jenkins.empresa.com): " JENKINS_URL
    read -p "Usuário do Jenkins: " JENKINS_USER
    read -sp "Token do Jenkins: " JENKINS_TOKEN
    echo
    read -p "Caminho dos repositórios Git (ex: ~/projetos): " REPOS_PATH
    read -p "Parâmetro padrão a buscar (ex: ECR_PATH): " DEFAULT_PARAM
    
    # Expande ~ para home
    REPOS_PATH="${REPOS_PATH/#\~/$HOME}"
    
    # Salva no config.ini
    cat > config.ini << EOF
[jenkins]
url = $JENKINS_URL
username = $JENKINS_USER
token = $JENKINS_TOKEN

[git]
repos_path = $REPOS_PATH

[search]
default_parameter = $DEFAULT_PARAM
EOF
    
    echo -e "${GREEN}✓ Configuração salva em config.ini${NC}"
    sleep 2
}

# Função para scan completo
scan_unified() {
    local PARAM="${1:-$DEFAULT_PARAM}"
    
    if [ -z "$PARAM" ]; then
        read -p "Nome do parâmetro a buscar: " PARAM
    fi
    
    echo -e "${BLUE}Iniciando scan completo para: $PARAM${NC}"
    
    OUTPUT_FILE="unified_report_${PARAM}_$(date +%Y%m%d_%H%M%S).txt"
    
    python3 unified_scanner.py \
        --jenkins-url "$JENKINS_URL" \
        --username "$JENKINS_USER" \
        --token "$JENKINS_TOKEN" \
        --repos-path "$REPOS_PATH" \
        --parameter "$PARAM" \
        --output "$OUTPUT_FILE"
    
    echo -e "${GREEN}✓ Scan completo! Relatório: $OUTPUT_FILE${NC}"
}

# Função para scan apenas Jenkins
scan_jenkins() {
    local PARAM="${1:-$DEFAULT_PARAM}"
    
    if [ -z "$PARAM" ]; then
        read -p "Nome do parâmetro a buscar: " PARAM
    fi
    
    echo -e "${BLUE}Iniciando scan do Jenkins para: $PARAM${NC}"
    
    OUTPUT_FILE="jenkins_report_${PARAM}_$(date +%Y%m%d_%H%M%S).txt"
    
    python3 jenkins_parameter_scanner.py \
        --jenkins-url "$JENKINS_URL" \
        --username "$JENKINS_USER" \
        --token "$JENKINS_TOKEN" \
        --parameter "$PARAM" \
        --output "$OUTPUT_FILE"
    
    echo -e "${GREEN}✓ Scan Jenkins completo! Relatório: $OUTPUT_FILE${NC}"
}

# Função para scan apenas Git
scan_git() {
    local PARAM="${1:-$DEFAULT_PARAM}"
    
    if [ -z "$PARAM" ]; then
        read -p "Nome do parâmetro a buscar: " PARAM
    fi
    
    echo -e "${BLUE}Iniciando scan dos repositórios Git para: $PARAM${NC}"
    
    OUTPUT_FILE="git_report_${PARAM}_$(date +%Y%m%d_%H%M%S).txt"
    
    python3 git_repository_scanner.py \
        --repos-path "$REPOS_PATH" \
        --parameter "$PARAM" \
        --output "$OUTPUT_FILE"
    
    echo -e "${GREEN}✓ Scan Git completo! Relatório: $OUTPUT_FILE${NC}"
}

# Função para múltiplos parâmetros
scan_multiple() {
    echo -e "${YELLOW}Digite os parâmetros a buscar (separados por espaço):${NC}"
    read -p "Parâmetros: " PARAMS
    
    for PARAM in $PARAMS; do
        echo
        echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
        echo -e "${BLUE}Buscando: $PARAM${NC}"
        echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
        scan_unified "$PARAM"
        echo
    done
    
    echo -e "${GREEN}✓ Todos os scans concluídos!${NC}"
}

# Função para verificar dependências
check_dependencies() {
    local missing=0
    
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}✗ Python 3 não encontrado${NC}"
        missing=1
    fi
    
    if ! command -v git &> /dev/null; then
        echo -e "${RED}✗ Git não encontrado${NC}"
        missing=1
    fi
    
    if ! python3 -c "import requests" 2>/dev/null; then
        echo -e "${YELLOW}⚠ Biblioteca 'requests' não encontrada${NC}"
        echo "Instalando..."
        pip3 install -r requirements.txt
    fi
    
    if [ $missing -eq 1 ]; then
        echo -e "${RED}Instale as dependências e tente novamente${NC}"
        exit 1
    fi
}

# Função para criar diretório de relatórios
create_reports_dir() {
    if [ ! -d "reports" ]; then
        mkdir -p reports
        echo -e "${GREEN}✓ Diretório 'reports' criado${NC}"
    fi
}

# Main
main() {
    show_banner
    
    # Verifica dependências
    check_dependencies
    
    # Cria diretório de relatórios
    create_reports_dir
    
    # Tenta ler configurações
    if ! read_config; then
        echo -e "${YELLOW}⚠ Arquivo config.ini não encontrado${NC}"
        echo -e "${YELLOW}Vamos configurar agora...${NC}"
        echo
        configure
        echo
        read_config
    fi
    
    # Loop do menu
    while true; do
        show_menu
        read -p "Escolha uma opção: " choice
        
        case $choice in
            1)
                echo
                scan_unified
                echo
                ;;
            2)
                echo
                scan_jenkins
                echo
                ;;
            3)
                echo
                scan_git
                echo
                ;;
            4)
                echo
                scan_multiple
                echo
                ;;
            5)
                echo
                configure
                echo
                ;;
            6)
                echo -e "${GREEN}Até logo!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}Opção inválida${NC}"
                ;;
        esac
        
        read -p "Pressione ENTER para continuar..."
        clear
        show_banner
    done
}

# Tratamento de argumentos
if [ $# -gt 0 ]; then
    # Se receber argumentos, executa direto sem menu
    check_dependencies
    
    case "$1" in
        unified)
            read_config
            scan_unified "$2"
            ;;
        jenkins)
            read_config
            scan_jenkins "$2"
            ;;
        git)
            read_config
            scan_git "$2"
            ;;
        config)
            configure
            ;;
        *)
            echo "Uso: $0 [unified|jenkins|git|config] [PARAMETRO]"
            echo "Ou execute sem argumentos para usar o menu interativo"
            exit 1
            ;;
    esac
else
    # Modo interativo
    main
fi
