# 📊 PyMetrics

[![CI](https://github.com/EnzoVieira3012/PyMetrics/actions/workflows/ci.yml/badge.svg)](https://github.com/EnzoVieira3012/PyMetrics/actions/workflows/ci.yml)

**Sistema de Análise de Performance de Repositórios GitHub**

PyMetrics consome a GitHub API para coletar, analisar e reportar métricas de performance de repositórios e desenvolvedores. Ferramenta **CLI + REST API** em Python, construída como projeto portfolio aplicando POO, decorators, generators e manipulação de arquivos.

O projeto é **open source**, licenciado sob a **MIT License**, gratuito e rodando em produção no **Render**.

---

## Funcionalidades

| Recurso | Descrição |
|---------|-----------|
| **Análise de repositórios** | Commits, issues, pull requests, contribuidores, linguagens |
| **Métricas de desenvolvedor** | Atividade, consistência, impacto, áreas de contribuição |
| **Exportação de relatórios** | CSV e JSON |
| **CLI interativo** | Menu de terminal para múltiplas análises |
| **REST API** | Endpoints HTTP para integrações externas |
| **Deploy no Render** | API sem banco de dados, pronta para produção |

### Modos de uso

| Modo | Como usar | O que faz |
|------|-----------|-----------|
| **CLI** | `python main.py` | Menu interativo: analisa repo/dev, exporta CSV/JSON |
| **REST API** | `python api/server.py` | Servidor HTTP com endpoints JSON (ver seção abaixo) |
| **API pronta** | Render | URL pública da API em produção |

---

## Conceitos Python Aplicados

> Construído com base na **Formação Python Fundamental** da DIO.

### Programação Orientada a Objetos

- **Classes e objetos** — `Repository`, `Commit`, `Developer`
- **Herança e polimorfismo** — relatórios em formatos diferentes (CSV, JSON)
- **Encapsulamento** — atributos protegidos e propriedades
- **Classes abstratas** — interface base para exportadores e analisadores

### Decorators

| Decorator | Função | Onde aplicado |
|-----------|--------|---------------|
| `@timer` | Mede e exibe o tempo de execução de funções | `get_repository`, `get_developer`, `iter_commits`, `get_repo_languages` |
| `@cache_result` | Armazena resultados em memória para chamadas repetidas | `get_repository`, `get_developer`, `get_open_issues_count` |
| `@log_execution` | Registra chamadas de funções em log | `_get` (camada HTTP central) |

- `@cache_result` fica **fora** de `@timer`: chamada cacheada nem loga tempo.
- `@log_execution` **sanitiza valores sensíveis** (kwargs contendo `token`, `password`, `secret`, `key` viram `***`) — o token nunca aparece nos logs.
- `iter_commits` **não** é cacheado (paginação pode crescer sem limite).

### Generators e Iterators

- Paginação **lazy** da GitHub API com `yield`
- Processa grandes volumes de commits sem carregar tudo em memória

---

## Métricas Analisadas

Os analisadores em `core/analyzer.py` herdam a base `Analyzer` e usam `lambda`, `filter()`, `sorted()` e `collections.Counter`:

| Analisador | Métricas |
|------------|----------|
| `CommitAnalyzer` | `total_commits`, `avg_changes_per_commit`, `most_common_day`, `most_common_hour`, `top_authors`, `commits_by_author`, `largest_commit`, `first_commit`, `last_commit` |
| `RepositoryAnalyzer` | `total_repos`, `total_stars`, `avg_stars`, `top_languages`, `most_popular`, `ranked_repos` |
| `DeveloperAnalyzer` | `total_devs`, `avg_repos_per_dev`, `top_developers`, `most_prolific` |

- `lambda` usado para `max`/`min` (`largest_commit`, `first_commit`, `most_popular`) e agregações (`sum`, `avg`).
- `Counter` + `_top_n` (DRY) gera rankings (`top_authors`, `top_languages`, `top_developers`).
- Coleções vazias retornam valores neutros (`0`, `0.0`, `None`, `[]`) sem crash.

---

## Exportação de Relatórios

`CsvExporter` e `JsonExporter` herdando de `Report` (polimorfismo):

```python
from core.analyzer import CommitAnalyzer
from exporters.csv_exporter import CsvExporter
from exporters.json_exporter import JsonExporter

metrics = CommitAnalyzer(commits).analyze()
print(CsvExporter(metrics).export())  # results/report_20260904_150956.csv
print(JsonExporter(metrics).export())  # results/report_20260904_150956.json
```

- Sem `path`, salva em `RESULTS_DIR` (default `results/`), pasta criada automaticamente.
- Nome padrão `report_YYYYMMDD_HHMMSS.csv` / `.json`.
- CSV achata dicts aninhados (chaves `a.b.c`) via `flatten_metrics` (DRY em `exporters/common.py`).
- JSON com `indent=2` + `ensure_ascii=False` (acentos preservados).
- Encoding `utf-8` em ambos.

---

## CLI (menu interativo)

Rode o entry point e escolha a opção:

```powershell
python main.py
```

Menu:

```
1. Analisar repositório   → owner + repo → métricas + exportar CSV/JSON
2. Analisar desenvolvedor → username → métricas + exportar CSV/JSON
3. Exportar relatório     → re-exporta a última análise
4. Sair
```

- Opção 1 usa `iter_commits` (paginação lazy) + `CommitAnalyzer`/`RepositoryAnalyzer`.
- Erros da API (`GithubClientError`) mostram mensagem amigável e voltam ao menu, sem crash.
- `Ctrl+C` (ou `Ctrl+Z`) encerra com "Até logo!".
- Logs dos decorators (`@timer`, `@log_execution`) aparecem no console (nível INFO).
- Comandos ficam em `cli/commands.py`; `main.py` só orquestra o loop.

---

## REST API (Flask)

Sobe o servidor HTTP (porta 5000):

```powershell
python api/server.py
```

| Método | Endpoint | Retorno |
|--------|----------|---------|
| `GET` | `/api/health` | `{"status": "ok", "timestamp": ...}` |
| `GET` | `/api/repos/<owner>/<name>` | Métricas do repositório + commits |
| `GET` | `/api/devs/<username>` | Métricas do desenvolvedor |
| `GET` | `/api/repos/<owner>/<name>/export?format=csv\|json` | Download do relatório |

Exemplo (PowerShell):

```powershell
Invoke-RestMethod http://localhost:5000/api/health
Invoke-RestMethod http://localhost:5000/api/repos/EnzoVieira3012/PyMetrics
Invoke-RestMethod -OutFile relatorio.json `
  "http://localhost:5000/api/repos/EnzoVieira3012/PyMetrics/export?format=json"
```

- Qualquer repo público funciona: troque `<owner>/<name>` na URL (ex: `torvalds/linux`).
- Erros retornam JSON amigável (`{"error": "..."}`) — sem traceback, sem token exposto.
- Reusa `GithubClient`, analyzers e exporters — zero duplicação de lógica.
- Deploy Render: start command `python api/server.py`, expor porta 5000.

---

## Instalação

> Requer **Python 3.10+** e um **GitHub Token** (escopo `repo`).

```bash
# Clone o repositório
git clone https://github.com/EnzoVieira3012/PyMetrics.git
cd PyMetrics

# Crie o ambiente virtual
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

# Instale as dependências
pip install -r requirements.txt

# Configure o token do GitHub
cp .env.example .env
# Edite .env e adicione seu token
```

### GitHub Token

1. Acesse [github.com/settings/tokens](https://github.com/settings/tokens)
2. Gere um **Personal Access Token** com escopo `repo`
3. Adicione no `.env`:

```
GITHUB_TOKEN=seu_token_aqui
```

---

## Configuração

Copie `.env.example` para `.env` e ajuste as variáveis suportadas:

| Variável | Default | Descrição |
|----------|---------|-----------|
| `GITHUB_TOKEN` | *(vazio)* | Token de autenticação da GitHub API |
| `GITHUB_API_URL` | `https://api.github.com` | URL base da GitHub API |
| `REQUEST_TIMEOUT` | `30` | Timeout das requisições HTTP (segundos) |
| `RESULTS_DIR` | `results` | Pasta de relatórios exportados |
| `LOG_LEVEL` | `INFO` | Nível de log (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

Valores vazios usam o default. O `.env` **nunca** é commitado — consulte `.env.example` para os placeholders.

```powershell
# Execute os testes
pytest tests/ -v

# Cobertura
pytest --cov=config tests/ --cov-report=term-missing
```

---

## Uso da API (smoke test)

Com o token configurado no `.env`, o client busca dados reais do GitHub:

```python
from core.github_client import GithubClient

client = GithubClient()

repo = client.get_repository("EnzoVieira3012", "PyMetrics")
print(repo.name, repo.stars, repo.url)

commits = list(client.iter_commits("EnzoVieira3012", "PyMetrics"))
print(len(commits))
```

- `iter_commits` usa **paginação lazy** (generators com `yield`) — uma página por vez, sem estourar memória.
- Erros da API viram `GithubClientError` com mensagem amigável (token inválido, não encontrado, rate limit).

---

## Uso

### CLI

```bash
python main.py
```

### REST API

```bash
python api/server.py
```

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| `GET` | `/api/repos/{owner}/{repo}` | Métricas de um repositório |
| `GET` | `/api/devs/{username}` | Métricas de um desenvolvedor |
| `GET` | `/api/repos/{owner}/{repo}/commits` | Commits com paginação |
| `GET` | `/api/health` | Status do servidor |

---

## Deploy no Render

O projeto **não utiliza banco de dados**: consome a GitHub API em tempo real, processa na memória e exporta para CSV/JSON. Por isso o deploy é leve e direto.

1. Faça push do código para o GitHub
2. No [Render](https://render.com/), crie um **Web Service**
3. Conecte o repositório `PyMetrics`
4. Build command: `pip install -r requirements.txt`
5. Start command: `python api/server.py`
6. Defina a variável de ambiente `GITHUB_TOKEN`
7. Faça o deploy ✅

---

## Arquitetura

```
PyMetrics/
├── main.py                    # Entry point da CLI
├── api/
│   └── server.py              # REST API (Flask)
├── core/
│   ├── models.py              # Repository, Commit, Developer, Analyzer, Report
│   ├── logging_setup.py       # Configuração base de logging
│   ├── errors.py              # GithubClientError — erros amigáveis da API
│   ├── analyzer.py            # Lógica de análise de performance
│   └── github_client.py       # Consumo da GitHub API com paginação
├── decorators/
│   ├── timer.py               # @timer — mede tempo de execução
│   ├── cache.py               # @cache_result — cache de resultados
│   └── logger.py              # @log_execution — log de chamadas
├── iterators/
│   └── lazy_commits.py        # Generator para paginação lazy de commits
├── exporters/
│   ├── csv_exporter.py        # Exportação para CSV
│   └── json_exporter.py       # Exportação para JSON
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Stack Tecnológica

- **Python 3.10+**
- **Flask** — REST API
- **GitHub API REST v3**
- **Render** — deployment
- **CSV / JSON** — exportação de dados

---

## Licença

Este projeto está licenciado sob a [MIT License](LICENSE).

---

## Contato

**Enzo Vieira**

- **LinkedIn**: [enzovieiratrabalho](https://www.linkedin.com/in/enzovieiratrabalho/)
- **GitHub**: [EnzoVieira3012](https://github.com/EnzoVieira3012)
- **Email**: [enzovieira.trabalho@outlook.com](mailto:enzovieira.trabalho@outlook.com)

*Projeto portfolio — Formação Python Fundamental DIO*
