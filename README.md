# 📊 PyMetrics

[![CI](https://github.com/EnzoVieira3012/PyMetrics/actions/workflows/ci.yml/badge.svg)](https://github.com/EnzoVieira3012/PyMetrics/actions/workflows/ci.yml)

**Sistema de Análise de Performance de Repositórios GitHub**

PyMetrics consome a GitHub API para coletar, analisar e reportar métricas de performance de repositórios e desenvolvedores. Ferramenta **CLI + REST API** em Python, construída como projeto portfolio aplicando POO, decorators, generators e manipulação de arquivos.

O projeto é **open source**, licenciado sob a **MIT License**, gratuito e rodando em produção no **Render**.

---

## 🚀 REST API — guia rápido

PyMetrics expõe **5 endpoints**. Cada um é uma pergunta que você faz pra API do GitHub, respondida em JSON.

### Como subir o servidor

```powershell
python -m api.server
```

Vai aparecer `Running on http://127.0.0.1:5000`. Pronto — a API está no ar. Abra no navegador:

**📘 Swagger (docs interativas): [http://localhost:5000/api/docs](http://localhost:5000/api/docs)**

Lá cada endpoint tem botão **Try it out**: preenche os campos, clica Execute, e vê a resposta real + o comando `curl` pronto pra copiar. Nada de teoria — testa na hora.

---

### 1️⃣ `GET /api/health` — "tá viva?"

O teste mais simples: só confirma que o servidor está de pé. Não toca o GitHub.

```
GET http://localhost:5000/api/health
```

Resposta:

```json
{"status":"ok","timestamp":"2026-09-04T21:20:52.961021+00:00"}
```

| Campo | O que significa |
|-------|-----------------|
| `status` | Sempre `"ok"` quando o servidor responde |
| `timestamp` | Hora exata (UTC) da resposta |

---

### 2️⃣ `GET /api/repos/{owner}/{name}` — "quanto esse repo rende?"

Métricas completas de QUALQUER repositório público do GitHub. Na URL, troque `{owner}` pelo dono e `{name}` pelo nome do repo. Não precisa ser seu, não precisa de permissão — qualquer repo público funciona.

```
GET http://localhost:5000/api/repos/yt-dlp/yt-dlp?limit=100
```

| Parâmetro | Obrigatório | O que é |
|-----------|-------------|---------|
| `owner` | ✅ | Dono do repo (ex: `yt-dlp`, `EnzoVieira3012`) |
| `name` | ✅ | Nome do repo (ex: `yt-dlp`, `PyMetrics`) |
| `limit` | ❌ | Quantos commits analisar (default `100`). Com `limit=5` analisa só os 5 mais recentes e responde rápido até em repo gigante |

Teste real com o `yt-dlp` (188 mil stars, 23 mil commits — analisou os 100 mais recentes em menos de 1 segundo):

```json
{
  "avg_stars": 188942,
  "commits": {
    "total_commits": 100,
    "top_authors": [["bashonly", 39], ["doe1080", 24], ["InvalidUsernameException", 7]],
    "commits_by_author": {"bashonly": 39, "doe1080": 24},
    "most_common_day": "Wednesday",
    "most_common_hour": 23,
    "first_commit": "b6590aaa1e3808155d69c9a79a797ae484163789",
    "largest_commit": "bbc809a1161d3bfca51fa36f59dda35556ee85a0",
    "last_commit": "bbc809a1161d3bfca51fa36f59dda35556ee85a0"
  },
  "total_stars": 188942,
  "top_languages": [["Python", 1]],
  "total_repos": 1,
  "most_popular": "https://github.com/yt-dlp/yt-dlp",
  "ranked_repos": ["https://github.com/yt-dlp/yt-dlp"],
  "sampled_commits": 100,
  "truncated": true
}
```

Lendo a resposta:

- `total_commits` `100` + `truncated` `true` → analisou os 100 mais recentes, corte ativo (repo tem 23 mil). `sampled_commits` confirma quantos entrou.
- `top_authors` → ranking de quem mais commita: `bashonly` 39 vezes.
- `total_stars` `188942` → estrelas do repo. `top_languages` → linguagens predominantes.
- `most_common_day` / `most_common_hour` → quando a galera mais commita.
- `first_commit` / `last_commit` / `largest_commit` → SHAs que marcam começo, fim e maior commit no recorte.

---

### 3️⃣ `GET /api/devs/{username}` — "quanto esse dev produz?"

Perfil de qualquer usuário público do GitHub. Troque `{username}` pelo nome de usuário.

```
GET http://localhost:5000/api/devs/yt-dlp
```

Teste real:

```json
{
  "total_devs": 1,
  "avg_repos_per_dev": 0,
  "top_developers": [],
  "most_prolific": "yt-dlp"
}
```

| Campo | O que significa |
|-------|-----------------|
| `total_devs` | Quantos devs entraram na análise (aqui: só ele) |
| `avg_repos_per_dev` | Média de repos por dev |
| `top_developers` | Ranking de mais produtivos (vazio quando analisa 1 dev só) |
| `most_prolific` | O dev mais ativo da análise |

---

### 4️⃣ `GET /api/repos/{owner}/{name}/export` — "me entrega um arquivo"

Igual ao endpoint 2, mas em vez de JSON na tela, **baixa um arquivo** com as métricas: CSV (planilha) ou JSON.

```
GET http://localhost:5000/api/repos/yt-dlp/yt-dlp/export?format=csv&limit=100
```

| Parâmetro | Obrigatório | O que é |
|-----------|-------------|---------|
| `owner` | ✅ | Dono do repo |
| `name` | ✅ | Nome do repo |
| `format` | ❌ | `csv` (default) ou `json` |
| `limit` | ❌ | Quantos commits analisar (default `100`) |

Teste real baixou: `yt-dlp_yt-dlp_report_20260904_212034.csv` — planilha com as métricas, pronta pra abrir no Excel.

- `format` inválido → erro `400` em JSON: `{"error": "formato inválido. Use csv ou json."}`
- O CSV acha dicts aninhados (chaves `a.b.c`) automagicamente.

---

### 5️⃣ `GET /api/repos/{owner}/{name}/commits` — "quero os commits em páginas"

Lista os commits de qualquer repo público com **paginação** (10, 20, 50 ou 100 por página — ou tudo de uma vez) e **ordenação** (por data ou autor).

```
GET http://localhost:5000/api/repos/yt-dlp/yt-dlp/commits?per_page=10&page=2
```

| Parâmetro | Obrigatório | O que é |
|-----------|-------------|---------|
| `owner` | ✅ | Dono do repo |
| `name` | ✅ | Nome do repo |
| `per_page` | ❌ | `10`, `20`, `50`, `100` ou `total` (default `20`) |
| `page` | ❌ | Número da página, começa em `1` |
| `sort` | ❌ | `date` (default) ou `author` |
| `order` | ❌ | `desc` (default, mais recentes primeiro) ou `asc` |

Teste real (yt-dlp, página 2, 10 itens):

```json
{
  "items": [
    {"sha": "bbc809a1...", "message": "Update README.md", "author": "bashonly",
     "email": "...", "date": "2026-09-03T12:41:10+00:00",
     "additions": 4, "deletions": 2, "files_changed": 1}
  ],
  "page": 2,
  "per_page": 10,
  "total_commits": 23997,
  "total_pages": 2400,
  "has_next": true,
  "has_prev": true,
  "mode": "paginated"
}
```

Lendo a resposta:

- `items` → os commits da página, cada um plano (sha, mensagem, autor, data, linhas, arquivos).
- `total_commits` / `total_pages` → contagem total e quantas páginas existem (aqui 23.997 commits / 2.400 páginas de 10).
- `has_next` / `has_prev` → navegação: `page=page+1` até `has_next` false.

Combinações úteis:

- `per_page=total` → puxa **tudo de uma vez**. Único modo com timeout estendido (`REQUEST_TIMEOUT_TOTAL`, default 120s) — nos demais o timeout normal vale.
- `sort=author&order=asc` → A-Z; `sort=author&order=desc` → Z-A.
- `sort=date&order=asc` → mais antigos primeiro; `desc` (default) → mais recentes.
- Página além do fim → `items` vazio, resposta `200` normal.
- Inválidos (`per_page=5`, `page=0`) → `400` JSON: `{"error": "..."}`.
- **Cache em disco**: repetir a mesma combinação (mesma página/ordem) não refaz requests ao GitHub.

---

### Dicas rápidas

- **Qualquer repo público funciona**: `yt-dlp/yt-dlp`, `torvalds/linux`, `facebook/react` — troca na URL e roda.
- **Repo gigante sem travar**: usa `?limit=` e responde rápido — sem paginar 23 mil commits no meio do caminho.
- **Cache em disco** (`.cache/pymetrics/`, vale 24h por env `CACHE_TTL_HOURS`): segunda chamada ao mesmo repo vem do disco, não toca o GitHub de novo.
- **Erros são JSON amigável** (`{"error": "..."}`) — nada de traceback feio, token nunca vaza.
- **Curl pronto**: no Swagger, cada endpoint te dá o comando `curl` copiável. Usa em script, Postman, o que quiser.

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
| **REST API** | `python -m api.server` | Servidor HTTP com endpoints JSON (ver guia no topo) |
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
| `@disk_cache_result` | Salva respostas JSON em disco (`.cache/`) por 24h — sobrevive a reinícios, não repete requests | `_get` (camada HTTP central) |
| `@log_execution` | Registra chamadas de funções em log | `_get` (camada HTTP central) |

- `@cache_result` fica **fora** de `@timer`: chamada cacheada nem loga tempo.
- `@log_execution` **sanitiza valores sensíveis** (kwargs contendo `token`, `password`, `secret`, `key` viram `***`) — o token nunca aparece nos logs.
- `iter_commits` usa **paginação lazy** + `limit`: busca só o que precisa, sem estourar a GitHub API em repos grandes (ex: yt-dlp tem 23k commits → 1 request com `limit=100`, não 230).

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
| `REQUEST_TIMEOUT_TOTAL` | `120` | Timeout só do modo `per_page=total` (segundos) — os demais mantêm `REQUEST_TIMEOUT` |
| `RESULTS_DIR` | `results` | Pasta de relatórios exportados |
| `LOG_LEVEL` | `INFO` | Nível de log (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |
| `CACHE_DIR` | `.cache/pymetrics` | Pasta do cache em disco das respostas da GitHub API |
| `CACHE_TTL_HOURS` | `24` | Validade do cache (horas) |
| `DEFAULT_LIMIT` | `100` | Limite padrão de commits analisados por requisição |

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
python -m api.server
```

Depois abra no navegador **http://localhost:5000/api/health** (status) ou a guia interativa **http://localhost:5000/api/docs** (Swagger, com botão de testar cada endpoint).

Endpoints: `GET /api/health`, `GET /api/repos/{owner}/{name}`, `GET /api/devs/{username}`, `GET /api/repos/{owner}/{name}/export?format=csv|json`, `GET /api/repos/{owner}/{name}/commits?per_page=&page=&sort=&order=` — cada um explicado com exemplo no topo do README.

---

## Deploy no Render

O projeto **não utiliza banco de dados**: consome a GitHub API em tempo real, processa na memória e exporta para CSV/JSON. Por isso o deploy é leve e direto.

1. Faça push do código para o GitHub
2. No [Render](https://render.com/), crie um **Web Service**
3. Conecte o repositório `PyMetrics`
4. Build command: `pip install -r requirements.txt`
5. Start command: `python -m api.server`
6. Defina a variável de ambiente `GITHUB_TOKEN`
7. Faça o deploy ✅

---

## Arquitetura

```
PyMetrics/
├── main.py                    # Entry point da CLI
├── api/
│   ├── server.py              # REST API (Flask)
│   └── pagination.py          # Paginação/filtros: enums + parse/ordenação
├── core/
│   ├── models.py              # Repository, Commit, Developer, Analyzer, Report
│   ├── logging_setup.py       # Configuração base de logging
│   ├── errors.py              # GithubClientError — erros amigáveis da API
│   ├── analyzer.py            # Lógica de análise de performance
│   └── github_client.py       # Consumo da GitHub API com paginação
├── decorators/
│   ├── timer.py               # @timer — mede tempo de execução
│   ├── cache.py               # @cache_result — cache em memória
│   ├── disk_cache.py          # @disk_cache_result — cache em disco (JSON, TTL)
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
