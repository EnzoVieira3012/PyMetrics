"""CLI commands: one function per menu action."""

from typing import Any

from core.analyzer import CommitAnalyzer, DeveloperAnalyzer, RepositoryAnalyzer
from exporters.csv_exporter import CsvExporter
from exporters.json_exporter import JsonExporter


def _export_report(metrics: dict[str, Any], fmt: str) -> str:
    """Export metrics via CsvExporter or JsonExporter."""
    if fmt == "csv":
        return CsvExporter(metrics).export()
    if fmt == "json":
        return JsonExporter(metrics).export()
    raise ValueError(f"Formato desconhecido: {fmt}")


def _ask_export(metrics: dict[str, Any]) -> None:
    """Ask the user whether to export and in which format."""
    choice = input("Exportar em CSV, JSON ou pular? [csv/json/s] ").strip().lower()
    if choice in ("csv", "json"):
        path = _export_report(metrics, choice)
        print(f"Relatório salvo em: {path}")
    else:
        print("Exportação pulada.")


def cmd_repo_analysis(client, unlimited_input=input) -> dict[str, Any]:
    """Menu action 1: analyze a repository, print summary, export optionally."""
    owner = input("Owner: ").strip()
    name = input("Repositório: ").strip()
    commits = list(client.iter_commits(owner, name))
    repo = client.get_repository(owner, name)
    metrics = RepositoryAnalyzer([repo]).analyze()
    metrics["commits"] = CommitAnalyzer(commits).analyze()

    print("\n--- Resumo do repositório ---")
    print(RepositoryAnalyzer([repo]).summary())
    print("\n--- Resumo dos commits ---")
    print(CommitAnalyzer(commits).summary())
    _ask_export(metrics)
    return metrics


def cmd_dev_analysis(client) -> dict[str, Any]:
    """Menu action 2: analyze a developer, print summary, export optionally."""
    username = input("Username: ").strip()
    dev = client.get_developer(username)
    metrics = DeveloperAnalyzer([dev]).analyze()

    print("\n--- Resumo do desenvolvedor ---")
    print(DeveloperAnalyzer([dev]).summary())
    _ask_export(metrics)
    return metrics


def cmd_export(last_metrics: dict[str, Any] | None) -> dict[str, Any] | None:
    """Menu action 3: re-export the last analysis."""
    if not last_metrics:
        print("Nenhuma análise feita ainda. Rode as opções 1 ou 2 primeiro.")
        return None
    choice = input("Exportar como CSV ou JSON? [csv/json] ").strip().lower()
    if choice in ("csv", "json"):
        path = _export_report(last_metrics, choice)
        print(f"Relatório salvo em: {path}")
    else:
        print("Formato não reconhecido. Nada exportado.")
    return last_metrics
