# 🚦 Guia de Decisão Rápida

## Qual scanner usar?

```
┌─────────────────────────────────────────────────────────────────┐
│  Você tem os repositórios Git clonados localmente?             │
└─────────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
               SIM                     NÃO
                │                       │
                ▼                       ▼
    ┌───────────────────────┐  ┌───────────────────────┐
    │ enhanced_jenkins_     │  │ jenkins_parameter_    │
    │ scanner.py            │  │ scanner.py            │
    │                       │  │                       │
    │ ✅ Vê Pipeline Script │  │ ✅ Vê Pipeline Script │
    │ ✅ Vê Pipeline SCM    │  │ ⚠️  Pipeline SCM:     │
    │    (lê Jenkinsfile)   │  │     só vê Git URL     │
    │                       │  │                       │
    │ --git-repos-path      │  │ (sem git-repos-path)  │
    │ ~/meus-repos          │  │                       │
    └───────────────────────┘  └───────────────────────┘
                │                       │
                └───────────┬───────────┘
                            ▼
                  ┌─────────────────────┐
                  │  Relatório Gerado   │
                  └─────────────────────┘
```

---

## 🎯 Fluxograma Detalhado

```
                        INÍCIO
                           │
                           ▼
        ┌──────────────────────────────────────┐
        │ Precisa buscar parâmetro em Jenkins? │
        └──────────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
            SIM                        NÃO
              │                         │
              ▼                         ▼
   ┌─────────────────────┐         [FIM]
   │ Tem acesso à API    │
   │ do Jenkins?         │
   │ (user + token)      │
   └─────────────────────┘
              │
         ┌────┴────┐
         │         │
        SIM       NÃO
         │         │
         │         ▼
         │    ┌─────────────────────────┐
         │    │ Gere token primeiro:    │
         │    │ Jenkins > Configure >   │
         │    │ API Token               │
         │    └─────────────────────────┘
         │
         ▼
   ┌──────────────────────────────┐
   │ Jobs são principalmente:     │
   └──────────────────────────────┘
         │
    ┌────┴────┐
    │         │
Pipeline    Pipeline
Script      from SCM
(inline)    (Git)
    │         │
    ▼         ▼
    │    ┌─────────────────────────┐
    │    │ Tem repos Git clonados? │
    │    └─────────────────────────┘
    │         │
    │    ┌────┴────┐
    │    │         │
    │   SIM       NÃO
    │    │         │
    └────┼─────────┘
         │         │
         ▼         ▼
 ┌────────────┐  ┌────────────┐
 │ enhanced_  │  │ jenkins_   │
 │ jenkins_   │  │ parameter_ │
 │ scanner.py │  │ scanner.py │
 │            │  │            │
 │ + git path │  │ sem git    │
 └────────────┘  └────────────┘
         │         │
         └────┬────┘
              ▼
      ┌──────────────┐
      │  RELATÓRIO   │
      │              │
      │ .txt + .json │
      └──────────────┘
              │
              ▼
      ┌──────────────────┐
      │ Satisfeito?      │
      └──────────────────┘
              │
         ┌────┴────┐
         │         │
        SIM       NÃO
         │         │
         ▼         ▼
       [FIM]  ┌─────────────────────┐
              │ Precisa mais        │
              │ detalhes no Git?    │
              └─────────────────────┘
                      │
                     SIM
                      │
                      ▼
              ┌──────────────────┐
              │ git_repository_  │
              │ scanner.py       │
              │                  │
              │ Busca só no Git  │
              └──────────────────┘
                      │
                      ▼
                    [FIM]
```

---

## 📊 Tabela de Comparação

| Característica | jenkins_parameter_scanner | enhanced_jenkins_scanner | git_repository_scanner | unified_scanner |
|---|---|---|---|---|
| **Busca em Jobs Jenkins** | ✅ | ✅ | ❌ | ✅ |
| **Busca em Git** | ❌ | ✅ (opcional) | ✅ | ✅ |
| **Detecta tipo de job** | ⚠️ Básico | ✅ Avançado | N/A | ✅ |
| **Pipeline Script inline** | ✅ | ✅ | ❌ | ✅ |
| **Pipeline from SCM** | ⚠️ Só Git URL | ✅ Lê Jenkinsfile | N/A | ✅ |
| **Análise cruzada** | ❌ | ⚠️ Parcial | ❌ | ✅ Completa |
| **Precisa repos Git?** | ❌ | ⚠️ Opcional | ✅ | ⚠️ Opcional |
| **Recomendado para** | Início rápido | Auditoria completa | Só Git | Análise profunda |

**Legenda:**
- ✅ = Funciona bem
- ⚠️ = Funciona com limitações
- ❌ = Não suporta

---

## 🎓 Casos de Uso

### Caso 1: "Quero começar rápido, não tenho repos locais"

```bash
python jenkins_parameter_scanner.py \
    --jenkins-url https://jenkins.empresa.com \
    --username admin \
    --token abc123 \
    --parameter ECR_PATH
```

**Resultado:**
- Lista jobs que usam ECR_PATH
- Para Pipeline Script: vê tudo
- Para Pipeline from SCM: só mostra Git URL

---

### Caso 2: "Tenho repos clonados, quero análise completa"

```bash
python enhanced_jenkins_scanner.py \
    --jenkins-url https://jenkins.empresa.com \
    --username admin \
    --token abc123 \
    --git-repos-path ~/projetos \
    --parameter ECR_PATH
```

**Resultado:**
- Lista jobs + lê Jenkinsfiles locais
- Análise completa de onde o parâmetro é usado
- Identifica Jenkinsfiles não encontrados

---

### Caso 3: "Quero análise cruzada profunda"

```bash
python unified_scanner.py \
    --jenkins-url https://jenkins.empresa.com \
    --username admin \
    --token abc123 \
    --repos-path ~/projetos \
    --parameter ECR_PATH
```

**Resultado:**
- Tudo do Caso 2 +
- Análise cruzada Jobs ↔ Repos
- Detecta órfãos (repos sem job, jobs sem repo)
- Recomendações

---

### Caso 4: "Só quero buscar nos repos Git"

```bash
python git_repository_scanner.py \
    --repos-path ~/projetos \
    --parameter ECR_PATH
```

**Resultado:**
- Lista repos que têm ECR_PATH
- Mostra arquivo, linha e contexto
- Não precisa de Jenkins

---

## 🔄 Workflow Recomendado

```
DIA 1: Preparação
├── 1. Gere token API do Jenkins
├── 2. Clone repositórios
│   └── Script: clone_all_repos.sh
└── 3. Configure config.ini

DIA 2: Primeira Auditoria
├── 1. Execute enhanced_jenkins_scanner.py
├── 2. Analise relatório
└── 3. Identifique repos faltantes

DIA 3: Auditoria Completa
├── 1. Clone repos faltantes
├── 2. Execute unified_scanner.py
└── 3. Análise cruzada

MANUTENÇÃO: Mensal
├── 1. Atualize repos (git pull)
├── 2. Re-execute scanners
└── 3. Compare com baseline
```

---

## ⚡ Comandos Rápidos

### Instalar
```bash
unzip jenkins-git-parameter-scanner.zip
chmod +x *.py *.sh
pip install -r requirements.txt
```

### Configurar
```bash
./run_scanner.sh config
# ou
cp config.ini.example config.ini
nano config.ini
```

### Executar (menu interativo)
```bash
./run_scanner.sh
```

### Executar (direto)
```bash
# Básico
./run_scanner.sh jenkins ECR_PATH

# Com Git
./run_scanner.sh unified ECR_PATH

# Múltiplos parâmetros
for param in ECR_PATH AWS_REGION IMAGE_TAG; do
    ./run_scanner.sh unified $param
done
```

---

## 🆘 FAQ Rápido

**P: Tenho 200 repos, preciso clonar todos?**
R: Não! Comece com `jenkins_parameter_scanner.py`, ele mostrará quais repos são relevantes. Clone apenas esses.

**P: Pipeline from SCM não mostra o Jenkinsfile**
R: Normal! Use `enhanced_jenkins_scanner.py` com `--git-repos-path` para ler do Git.

**P: Posso buscar em workspace dos agents?**
R: ❌ Não recomendado! Dados incompletos e distribuídos. Use API + Git.

**P: Como atualizar repos diariamente?**
R: Script simples:
```bash
cd ~/repos
for d in */; do (cd "$d" && git pull); done
```

**P: Scanner lento (muitos jobs)**
R: Normal para 100+ jobs. Execute de noite ou use cache:
```bash
# Salva resultado
python enhanced_jenkins_scanner.py ... > scan.txt
# Analisa depois
grep "ECR_PATH" scan.txt
```

---

## 📞 Próximos Passos

1. ✅ Escolha o scanner adequado (veja tabela acima)
2. ✅ Configure credenciais
3. ✅ Execute primeira auditoria
4. ✅ Analise relatório
5. ✅ Tome ações corretivas
6. ✅ Agende execução periódica

---

**Criado para facilitar suas auditorias Jenkins! 🚀**
