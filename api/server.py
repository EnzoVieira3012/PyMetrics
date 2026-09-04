"""PyMetrics REST API (Flask)."""

from datetime import datetime, timezone

from flask import Flask, jsonify, request, send_file
from flask_swagger_ui import get_swaggerui_blueprint

import config
from api.pagination import (
    PageSize,
    paginate,
    parse_params,
    sort_commits,
)
from core.analyzer import CommitAnalyzer, DeveloperAnalyzer, RepositoryAnalyzer
from core.errors import GithubClientError
from core.github_client import GithubClient
from exporters.common import default_path
from exporters.csv_exporter import CsvExporter
from exporters.json_exporter import JsonExporter


def _build_spec() -> dict:
    """OpenAPI 3 specification served at /swagger.json."""
    return {
        "openapi": "3.0.3",
        "info": {
            "title": "PyMetrics API",
            "description": "Análise de performance de repositórios e devs GitHub",
            "version": "1.0.0",
        },
        "paths": {
            "/api/health": {
                "get": {
                    "summary": "Verifica se a API está de pé",
                    "responses": {"200": {"description": "OK"}},
                }
            },
            "/api/repos/{owner}/{name}": {
                "get": {
                    "summary": "Métricas de um repositório",
                    "parameters": [
                        {
                            "name": "owner",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                        {
                            "name": "name",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "schema": {"type": "integer", "default": 100},
                        },
                    ],
                    "responses": {"200": {"description": "Métricas do repositório"}},
                }
            },
            "/api/devs/{username}": {
                "get": {
                    "summary": "Métricas de um desenvolvedor",
                    "parameters": [
                        {
                            "name": "username",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {"200": {"description": "Métricas do dev"}},
                }
            },
            "/api/repos/{owner}/{name}/commits": {
                "get": {
                    "summary": "Lista commits paginada e ordenável",
                    "parameters": [
                        {
                            "name": "owner",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                        {
                            "name": "name",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                        {
                            "name": "per_page",
                            "in": "query",
                            "schema": {
                                "type": "integer",
                                "enum": [10, 20, 50, 100, "total"],
                                "default": 20,
                            },
                        },
                        {
                            "name": "page",
                            "in": "query",
                            "schema": {"type": "integer", "minimum": 1, "default": 1},
                        },
                        {
                            "name": "sort",
                            "in": "query",
                            "schema": {"type": "string", "enum": ["date", "author"]},
                        },
                        {
                            "name": "order",
                            "in": "query",
                            "schema": {"type": "string", "enum": ["asc", "desc"]},
                        },
                    ],
                    "responses": {
                        "200": {"description": "Página de commits com metadados"},
                        "400": {"description": "Parâmetro inválido"},
                    },
                }
            },
            "/api/repos/{owner}/{name}/export": {
                "get": {
                    "summary": "Exporta métricas do repositório (csv ou json)",
                    "parameters": [
                        {
                            "name": "owner",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                        {
                            "name": "name",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                        {
                            "name": "format",
                            "in": "query",
                            "schema": {"type": "string", "enum": ["csv", "json"]},
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "schema": {"type": "integer", "default": 100},
                        },
                    ],
                    "responses": {
                        "200": {"description": "Arquivo exportado"},
                        "400": {"description": "Formato inválido"},
                    },
                }
            },
        },
    }


def create_app(client: GithubClient | None = None) -> Flask:
    """App factory: build and configure the Flask application."""
    app = Flask(__name__)
    if client is None:
        client = GithubClient()

    def _serialize_commit(commit) -> dict:
        """Flat JSON-safe dict for one Commit (Flask jsonify can't read properties)."""
        return {
            "sha": commit.sha,
            "message": commit.message,
            "author": commit.author,
            "email": commit.author_email,
            "date": commit.date.isoformat(),
            "additions": commit.additions,
            "deletions": commit.deletions,
            "files_changed": commit.files_changed,
        }

    def _limit() -> int | None:
        raw = request.args.get("limit")
        if raw is None:
            return config.DEFAULT_LIMIT
        try:
            return max(1, int(raw))
        except ValueError:
            return config.DEFAULT_LIMIT

    @app.get("/api/health")
    def health():
        return jsonify(
            {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}
        )

    @app.get("/api/repos/<owner>/<name>")
    def repo_metrics(owner: str, name: str):
        repo = client.get_repository(owner, name)
        commits = list(client.iter_commits(owner, name, limit=_limit()))
        metrics = RepositoryAnalyzer([repo]).analyze()
        metrics["commits"] = CommitAnalyzer(commits).analyze()
        metrics["truncated"] = len(commits) >= _limit()
        metrics["sampled_commits"] = len(commits)
        return jsonify(metrics)

    @app.get("/api/devs/<username>")
    def dev_metrics(username: str):
        dev = client.get_developer(username)
        return jsonify(DeveloperAnalyzer([dev]).analyze())

    @app.get("/api/repos/<owner>/<name>/export")
    def repo_export(owner: str, name: str):
        fmt = request.args.get("format", "csv")
        if fmt not in ("csv", "json"):
            return jsonify({"error": "formato inválido. Use csv ou json."}), 400
        commit_list = list(client.iter_commits(owner, name, limit=_limit()))
        repo = client.get_repository(owner, name)
        metrics = RepositoryAnalyzer([repo]).analyze()
        metrics["commits"] = CommitAnalyzer(commit_list).analyze()
        slug = f"{owner}_{name}"
        path = default_path(fmt, prefix=slug).resolve()
        if fmt == "csv":
            CsvExporter(metrics).export(str(path))
            mimetype = "text/csv"
        else:
            JsonExporter(metrics).export(str(path))
            mimetype = "application/json"
        return send_file(
            path, as_attachment=True, download_name=path.name, mimetype=mimetype
        )

    @app.get("/api/repos/<owner>/<name>/commits")
    def repo_commits(owner: str, name: str):
        params = parse_params(
            per_page=request.args.get("per_page", "20"),
            page=request.args.get("page", "1"),
            sort=request.args.get("sort", "date"),
            order=request.args.get("order", "desc"),
        )
        total_mode = params["per_page"] == PageSize.TOTAL.value
        limit = None if total_mode else params["per_page"] * params["page"]
        timeout = config.REQUEST_TIMEOUT_TOTAL if total_mode else None
        commits = list(client.iter_commits(owner, name, limit=limit, timeout=timeout))
        ordered = sort_commits(commits, params["sort"], params["order"])
        serialized = [_serialize_commit(c) for c in ordered]
        if total_mode:
            return jsonify(
                {"items": serialized, "mode": "total", "total_commits": len(serialized)}
            )
        total = client.get_commit_count(owner, name)
        result = paginate(serialized, params["page"], params["per_page"], total=total)
        result["mode"] = "paginated"
        return jsonify(result)

    @app.errorhandler(GithubClientError)
    def handle_github_error(exc: GithubClientError):
        return jsonify({"error": str(exc)}), 400

    @app.errorhandler(ValueError)
    def handle_value_error(exc: ValueError):
        return jsonify({"error": str(exc)}), 400

    @app.errorhandler(404)
    def handle_not_found(_):
        return jsonify({"error": "recurso não encontrado"}), 404

    @app.errorhandler(500)
    def handle_server_error(exc):
        app.logger.error("Erro interno: %s", exc)
        return jsonify({"error": "erro interno do servidor"}), 500

    @app.get("/swagger.json")
    def swagger_spec():
        return jsonify(_build_spec())

    swagger_bp = get_swaggerui_blueprint("/api/docs", "/swagger.json")
    app.register_blueprint(swagger_bp)

    return app


if __name__ == "__main__":
    create_app().run(host="0.0.0.0", port=5000)
