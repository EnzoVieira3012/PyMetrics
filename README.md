# 📊 PyMetrics

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

### Comparação de uso

| Comando | O que faz |
|---------|-----------|
| `python main.py repo {owner}/{repo}` | Analisa um repositório específico |
| `python main.py dev {username}` | Analisa as contribuições de um desenvolvedor |
| `python main.py export csv` | Gera relatório em CSV |
| `python main.py export json` | Gera relatório em JSON |

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
