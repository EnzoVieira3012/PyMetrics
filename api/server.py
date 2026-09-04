"""PyMetrics REST API (Flask)."""

from datetime import datetime

from flask import Flask, jsonify, request, send_file

from core.analyzer import CommitAnalyzer, DeveloperAnalyzer, RepositoryAnalyzer
from core.errors import GithubClientError
from core.github_client import GithubClient
from exporters.common import default_path
from exporters.csv_exporter import CsvExporter
from exporters.json_exporter import JsonExporter


def create_app(client: GithubClient | None = None) -> Flask:
    """App factory: build and configure the Flask application."""
    app = Flask(__name__)
    if client is None:
        client = GithubClient()

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

    @app.get("/api/repos/<owner>/<name>")
    def repo_metrics(owner: str, name: str):
        repo = client.get_repository(owner, name)
        commits = list(client.iter_commits(owner, name))
        metrics = RepositoryAnalyzer([repo]).analyze()
        metrics["commits"] = CommitAnalyzer(commits).analyze()
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
        commit_list = list(client.iter_commits(owner, name))
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
        return send_file(path, as_attachment=True, download_name=path.name, mimetype=mimetype)

    @app.errorhandler(GithubClientError)
    def handle_github_error(exc: GithubClientError):
        return jsonify({"error": str(exc)}), 400

    @app.errorhandler(404)
    def handle_not_found(_):
        return jsonify({"error": "recurso não encontrado"}), 404

    @app.errorhandler(500)
    def handle_server_error(exc):
        app.logger.error("Erro interno: %s", exc)
        return jsonify({"error": "erro interno do servidor"}), 500

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)